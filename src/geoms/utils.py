"""Write data into GEOMS compliant HDF5 files.

This code has been adapted from the PROFFASTpylot (https://doi.org/10.21105/joss.06481)
which is licensed under the GNU General Public License version 3. The authors of the
original code are Lena Feld, Benedikt Herkommer, Darko Dubravica affiliated with the
Karlsruhe Institut of Technology (KIT)."""

import datetime
import glob
import os
import re
from typing import Any, Optional
import numpy as np
import math
import pandas as pd
import polars as pl
import tum_esm_utils
from src import bundle
import src


def geoms_times_to_datetime(times: list[float]) -> list[datetime.datetime]:
    """Transforms GEOMS DATETIME variable to dt.datetime instances
    (input is seconds, since 1/1/2000 at 0UT)"""
    t_ref = datetime.datetime(2000, 1, 1)
    return [t_ref + datetime.timedelta(seconds=t) for t in times]


def datetimes_to_geoms_times(times: list[datetime.datetime]) -> list[float]:
    """Transforms dt.datetime instances to GEOMS DATETIME
    (output is seconds, since 1/1/2000 at 0UT)"""
    t_ref = datetime.datetime(2000, 1, 1)
    return [(t - t_ref).total_seconds() for t in times]


def load_comb_invparms_df(
    results_folder: str,
    sensor_id: str,
    geoms_config: src.types.GEOMSConfig,
    retrieval_algorithm: src.types.RetrievalAlgorithm,
) -> Optional[pl.DataFrame]:
    df = bundle.load_results.load_results_directory(
        results_folder,
        sensor_id,
        retrieval_algorithm=retrieval_algorithm,
        parse_dc_timeseries=geoms_config.parse_dc_timeseries,
        keep_julian_dates=True,
    )
    if df is None:
        return None

    # convert altim from m to km
    df = df.with_columns(pl.col("alt").truediv(1000).alias("altim"))

    # fill out of bounds values
    fill_value = -900_000
    for gas, max_value in [
        ("XCO2", 10_000),
        ("XCH4", 10),
        ("XCO", 10_000),
        ("XH2O", 10_000),
    ]:
        df = df.with_columns(
            pl.when(pl.col(gas).le(0.0) | pl.col(gas).ge(max_value))
            .then(fill_value)
            .otherwise(pl.col(gas))
            .alias(gas)
        )

    # filter based on DC amplitude
    if geoms_config.parse_dc_timeseries and (
        retrieval_algorithm
        not in [
            "proffast-2.2",
            "proffast-2.3",
        ]
    ):
        # fmt: off
        df = df.with_columns(
            pl.col("ch1_fwd_dc_mean").add(pl.col("ch1_bwd_dc_mean")).mul(0.5).abs() \
                .ge(geoms_config.dc_min_xco2).alias("xco2_dc_valid"),
                
            pl.col("ch1_fwd_dc_mean").add(pl.col("ch1_bwd_dc_mean")).mul(0.5).abs() \
                .ge(geoms_config.dc_min_xch4).alias("xch4_dc_valid"),
                
            pl.col("ch1_fwd_dc_mean").add(pl.col("ch1_bwd_dc_mean")).mul(0.5).abs() \
                .ge(geoms_config.dc_min_xh2o).alias("xh2o_dc_valid"),
                
            pl.col("ch2_fwd_dc_mean").add(pl.col("ch2_bwd_dc_mean")).mul(0.5).abs() \
                .ge(geoms_config.dc_min_xco).alias("xco_dc_valid"),
        )
        # fmt: on
        df = df.with_columns(
            pl.when("xco2_dc_valid").then(pl.col("XCO2")).otherwise(fill_value).alias("XCO2"),
            pl.when("xch4_dc_valid").then(pl.col("XCH4")).otherwise(fill_value).alias("XCH4"),
            pl.when("xh2o_dc_valid").then(pl.col("XH2O")).otherwise(fill_value).alias("XH2O"),
            pl.when("xco_dc_valid").then(pl.col("XCO")).otherwise(fill_value).alias("XCO"),
        )
        df = df.filter(
            pl.col("xco2_dc_valid")
            | pl.col("xch4_dc_valid")
            | pl.col("xh2o_dc_valid")
            | pl.col("xco_dc_valid")
        ).drop(
            "xco2_dc_valid",
            "xch4_dc_valid",
            "xh2o_dc_valid",
            "xco_dc_valid",
        )

    # filter based on SZA and XAIR
    if geoms_config.max_sza is not None:
        df = df.filter(pl.col("sza").le(geoms_config.max_sza))
    if geoms_config.min_xair is not None:
        df = df.filter(pl.col("XAIR").ge(geoms_config.min_xair))
    if geoms_config.max_xair is not None:
        df = df.filter(pl.col("XAIR").le(geoms_config.max_xair))

    return df


# https://github.com/coccon/proffastpylot/blob/2.4.1-2/prfpylot/output/hdf_geoms_writer.py#L1563
# identical to PROFFASTpylot 2.4.1-2
def get_ils_form_preprocess_inp(
    results_folder: str, date: datetime.date
) -> tuple[float, float, float, float]:
    """Return ILS from preprocess input file."""
    search_path = os.path.join(
        results_folder, "input_files", f"preprocess*{date.strftime('%y%m%d')}.inp"
    )
    file_list = glob.glob(search_path)
    if len(file_list) == 0:
        raise FileNotFoundError(f"No preprocess input file found for {date}")
    else:
        preprocess_input_file = file_list[0]

    with open(preprocess_input_file, "r") as f:
        lines = f.readlines()

    # go to second $ (counter i)
    # and read the following two lines (counter j)
    i = 0
    j = 0
    ils: list[Any] = []
    for line in lines:
        if line.startswith("$"):
            i += 1
            continue
        if i == 2:
            if j >= 2:
                break  # read only 2 lines
            tmp_ils = np.array(line.split(" ")).astype(float)
            ils.extend(tmp_ils)
            j += 1

    assert len(ils) == 4
    return (float(ils[0]), float(ils[1]), float(ils[2]), float(ils[3]))


# https://github.com/coccon/proffastpylot/blob/2.4.1-2/prfpylot/output/hdf_geoms_writer.py#L377
# identical to PROFFASTpylot 2.4.1-2
def load_vmr_file(results_folder: str, date: datetime.date, sensor_id: str) -> pd.DataFrame:
    # The content of the output VMR file is read separately for each
    # measurement day.
    # Each VMR file (i.e. VMR_fast_out.dat) contains:
    # 0: "Index", 1: "Altitude", 2: "H2O", 3: "HDO", 4: "CO2", 5: "CH4",
    # 6: "N2O", 7: "CO", 8: "O2", 9: "HF"

    paths: list[str] = [
        os.path.join(
            results_folder,
            "raw_output_proffast",
            f"{sensor_id}{date.strftime('%y%m%d')}-VMR_fast_out.dat",
        ),
        os.path.join(
            results_folder,
            "analysis",
            "pT",
            f"{sensor_id}{date.strftime('%y%m%d')}-VMR_fast_out.dat",
        ),
    ]

    names = ["Index", "Altitude", "H2O", "HDO", "CO2", "CH4", "N2O", "CO", "O2", "HF"]
    for path in paths:
        if os.path.exists(path):
            return pd.read_csv(  # pyright: ignore[reportUnknownMemberType]
                path,
                header=None,
                skipinitialspace=True,
                usecols=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
                names=names,
                sep=" ",
                engine="python",
            )
    raise FileNotFoundError(
        f"VMR file for {sensor_id} on {date} not found in {results_folder}. "
        + f"Looked for {[p.replace(results_folder, '') for p in paths]}"
    )


# https://github.com/coccon/proffastpylot/blob/2.4.1-2/prfpylot/output/hdf_geoms_writer.py#L404
# identical to PROFFASTpylot 2.4.1-2
def load_pt_file(results_folder: str, date: datetime.date, sensor_id: str) -> pd.DataFrame:
    # The content of the pT output file is read separately for
    # each measurement day.
    # Each pT file (i.e. pT_fast_out.dat) contains:
    # 0: "Index", 1: "Altitude", 2: "Temperature", 3: "Pressure",
    # 4: "DryAirColumn", 5: "H2O", 6: "HDO"

    paths: list[str] = [
        os.path.join(
            results_folder,
            "raw_output_proffast",
            f"{sensor_id}{date.strftime('%y%m%d')}-pT_fast_out.dat",
        ),
        os.path.join(
            results_folder,
            "analysis",
            "pT",
            f"{sensor_id}{date.strftime('%y%m%d')}-pT_fast_out.dat",
        ),
    ]
    for path in paths:
        if os.path.exists(path):
            return pd.read_csv(  # pyright: ignore[reportUnknownMemberType]
                path,
                header=0,
                skipinitialspace=True,
                usecols=[0, 1, 2, 3, 4, 5, 6],
                names=["Index", "Altitude", "Tem", "Pre", "DAC", "H2O", "HDO"],
                sep=" ",
                engine="python",
            )
    raise FileNotFoundError(
        f"pT file for {sensor_id} on {date} not found in {results_folder}. "
        + f"Looked for {[p.replace(results_folder, '') for p in paths]}"
    )


# https://github.com/coccon/proffastpylot/blob/2.4.1-2/prfpylot/output/hdf_geoms_writer.py#L443
# identical to PROFFASTpylot 2.4.1-2
def load_column_sensitivity_file(
    results_folder: str, date: datetime.date, sensor_id: str
) -> tuple[
    list[str],
    np.ndarray[Any, Any],
    np.ndarray[Any, Any],
    np.ndarray[Any, Any],
    np.ndarray[Any, Any],
]:
    # The column sensivity file (i.e. *colsens.dat") contains the vertical
    # profile of the pressure and
    # the sensitivities for each species (these are H2O, HDO, CO2, CH4,
    # N2O, CO, O2, HF) as function of the SZA.
    # alt [km], p [mbar], SZA [rad]:
    # 0.000E+00, 3.965E-01, 5.607E-01, 6.867E-01, 7.930E-01, 8.866E-01,
    # 9.712E-01, 1.049E+00,
    # 1.121E+00, 1.189E+00, 1.254E+00, 1.315E+00, 1.373E+00, 1.430E+00,
    # 1.484E+00

    sza: Any = []
    alt: Any = []
    pre: Any = []
    sen: Any = []

    # Get path and name for the column sensitivity file of a certain day.

    colsens_filename = f"{sensor_id}{date.strftime('%y%m%d')}-colsens.dat"

    paths = [
        os.path.join(results_folder, "raw_output_proffast", colsens_filename),
        os.path.join(results_folder, colsens_filename),
    ]
    path: Optional[str] = None
    for p in paths:
        if os.path.exists(p):
            path = p
            break
    if path is None:
        raise FileNotFoundError(
            f"Column sensitivity file for {sensor_id} on {date} not found in {results_folder}. "
            + f"Looked for {[p.replace(results_folder, '') for p in paths]}"
        )

    full_file_lines = (
        tum_esm_utils.files.load_file(path).replace("\t", " ").strip("\n ").split("\n")
    )
    gas_names: list[str] = []
    for i in range(1, len(full_file_lines)):
        if full_file_lines[i].strip(" ") == "$":
            gas_names.append(full_file_lines[i - 1].strip("\"' "))

    for gas in ["H2O", "CO2", "CH4"]:
        if gas not in gas_names:
            raise ValueError(f"Column sensitivity file is corrupted, {gas} header not found.")

    # Read pressure and sensitivities as function of the altitude and SZA.

    with open(path, "r") as f:
        for i in range(len(gas_names)):  # H2O, HDO, CO2, CO2_STR, CH4, CH4_S5P, N2O, CO, O2, HF
            sza.append([])
            alt.append([])
            pre.append([])
            sen.append([])

            for j in range(6):  # 6 header lines for each species
                header = f.readline()  # skip header line
                if j == 3:  # read SZA [rad] values in the third line
                    header = re.sub(" +", "\t", header)
                    sza[i] = np.array(header.split("\t")[3:])  # SZA header/columns
                    sza[i] = sza[i].astype(float)  # string to float

            for j in range(49):  # number of altitude levels
                line = f.readline()[1:-1]  # skip first empty
                # space and carriage return character at the end
                line = re.sub(" +", ",", line)  # replace empty spaces
                # by a comma
                line_cols = line.split(",")  # split line into columns

                alt[i].append(line_cols[0])  # altitude (first column)
                pre[i].append(line_cols[1])  # pressure (second column)

                sen[i].append([])
                for k in range(2, len(line_cols)):  # SZA (third column
                    # upwards, total 15 columns)
                    sen[i][j].append(float(line_cols[k]))

    sza = np.array(sza, dtype=float)  # SZA [deg]
    alt = np.array(alt, dtype=float)  # altitude [km]
    pre = np.array(pre, dtype=float)  # pressure [mbar]
    sen = np.array(sen, dtype=float)  # sensitivity

    return gas_names, sza, alt, pre, sen


# https://github.com/coccon/proffastpylot/blob/2.4.1-2/prfpylot/output/hdf_geoms_writer.py#L509
# identical to PROFFASTpylot 2.4.1-2
def load_interpolated_column_sensitivity_file(
    results_folder: str,
    date: datetime.date,
    sensor_id: str,
    szas: np.ndarray[Any, Any],
) -> dict[str, list[list[float]]]:
    gas_names, sza, alt, pre, sen = load_column_sensitivity_file(results_folder, date, sensor_id)  # pyright: ignore[reportUnusedVariable]

    gas_sens: dict[str, list[list[float]]] = {}

    for k in range(len(gas_names)):  # H2O, HDO, CO2, CO2_STR, CH4, CH4_S5P, N2O, CO, O2, HF
        gas_sens[gas_names[k]] = []

        for i in range(len(szas)):
            # number of measurements

            gas_sens[gas_names[k]].append([])

            SZA_app_rad = szas[i] * 2.0 * math.pi / 360.0
            # SZA_app_deg = appSZA[i]

            for j in range(len(sza[k]) - 1):  # number SZA angels
                SZA_sen_rad_1 = sza[k][j]
                # SZA_sen_deg_1 = sza[k][j] / 2.0 / math.pi * 360.
                SZA_sen_rad_2 = sza[k][j + 1]
                # SZA_sen_deg_2 = sza[k][j+1] / 2.0 / math.pi * 360.
                SZA_dif_rad = SZA_sen_rad_2 - SZA_sen_rad_1
                # SZA_dif_deg = SZA_sen_deg_2 - SZA_sen_deg_1

                if SZA_app_rad >= SZA_sen_rad_1 and SZA_app_rad <= SZA_sen_rad_2:
                    for h in range(len(alt[k])):
                        gas_1 = sen[k][h][j]
                        gas_2 = sen[k][h][j + 1]
                        gas_dif = gas_2 - gas_1

                        m_rad = gas_dif / SZA_dif_rad
                        # m_deg = gas_dif/SZA_dif_deg

                        b_gas = gas_1 - m_rad * SZA_sen_rad_1

                        # gas interpolation
                        gas_int = m_rad * SZA_app_rad + b_gas
                        gas_sens[gas_names[k]][i].append(gas_int)

                elif j == len(sza[k]) - 2 and SZA_app_rad > sza[k][len(sza) - 1]:
                    for h in range(len(alt[k])):
                        gas_1 = sen[k][h][j]
                        gas_2 = sen[k][h][j + 1]
                        gas_dif = gas_2 - gas_1

                        m_rad = gas_dif / SZA_dif_rad
                        # m_deg = gas_dif/SZA_dif_deg

                        b_gas = gas_1 - m_rad * SZA_sen_rad_1

                        # gas extrapolation
                        gas_int = m_rad * SZA_app_rad + b_gas
                        gas_sens[gas_names[k]][i].append(gas_int)

    return gas_sens


# https://github.com/coccon/proffastpylot/blob/2.4.1-2/prfpylot/output/hdf_geoms_writer.py#L581
# equivalent to PROFFASTpylot 2.4.1-2
def calculate_column_uncertainty(df: pl.DataFrame) -> pl.DataFrame:
    window_size = 11
    side_window_size = window_size // 2
    new_df = df.clone()

    for gas in ["XH2O", "XCO2", "XCH4", "XCO"]:
        gas_df = df.select("JulianDate", gas).filter(pl.col(gas).gt(0.0))
        gas_column: list[float] = gas_df[gas].to_list()

        rolling_mean: list[float] = [-900_000.0] * len(gas_column)
        for i in range(side_window_size, len(gas_column) - side_window_size):
            window = gas_column[i - side_window_size : i + side_window_size + 1]
            rolling_mean[i] = sum(window) / window_size

        gas_uncertainties: list[float] = [-900_000.0] * len(gas_column)
        for i in range(side_window_size * 2, len(gas_column) - (side_window_size * 2)):
            rolling_mean_window = rolling_mean[i - side_window_size : i + side_window_size + 1]
            window = gas_column[i - side_window_size : i + side_window_size + 1]
            squared_error = [
                math.pow(window[i] - rolling_mean_window[i], 2) for i in range(window_size)
            ]
            root_mean_squared_error = math.sqrt(sum(squared_error) / (window_size - 1))
            gas_uncertainties[i] = root_mean_squared_error

        new_df = new_df.join(
            pl.DataFrame(
                {"JulianDate": gas_df["JulianDate"], f"{gas}_uncertainty": gas_uncertainties}
            ),
            how="left",
            on="JulianDate",
        ).fill_null(-900_000.0)

    return new_df
