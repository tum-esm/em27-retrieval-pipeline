import datetime
import glob
import os
import re
from typing import Any, Optional
import numpy as np
import math
import pandas as pd
import polars as pl
from src import bundle
from . import constants


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


def load_comb_invparms_df(results_folder: str, sensor_id: str) -> pl.DataFrame:
    df = bundle.load_results.load_results_directory(
        results_folder,
        sensor_id,
        parse_dc_timeseries=constants.PARSE_DC_TIMESERIES,
        keep_julian_dates=True,
    )
    assert df is not None

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
            pl.when(pl.col(gas).lt(0.0) | pl.col(gas).gt(max_value))
            .then(fill_value)
            .otherwise(pl.col(gas))
            .alias(gas)
        )

    # filter based on DC amplitude
    if constants.PARSE_DC_TIMESERIES:
        df = df.with_columns(
            pl.col("ch1_fwd_dc_mean")
            .add(pl.col("ch1_bwd_dc_mean"))
            .mul(0.5)
            .abs()
            .ge(0.05)
            .alias("ch1_valid"),
            pl.col("ch2_fwd_dc_mean")
            .add(pl.col("ch2_bwd_dc_mean"))
            .mul(0.5)
            .abs()
            .ge(0.01)
            .alias("ch2_valid"),
        )
        df = df.with_columns(
            pl.when("ch1_valid").then(pl.col("XCO2")).otherwise(fill_value).alias("XCO2"),
            pl.when("ch1_valid").then(pl.col("XCH4")).otherwise(fill_value).alias("XCH4"),
            pl.when("ch1_valid").then(pl.col("XH2O")).otherwise(fill_value).alias("XH2O"),
            pl.when("ch2_valid").then(pl.col("XCO")).otherwise(fill_value).alias("XCO"),
        )
        df = df.filter(pl.col("ch1_valid") | pl.col("ch2_valid"))
        df = df.drop("ch1_valid", "ch2_valid")

    # filter based on SZA and XAIR
    if constants.MIN_SZA is not None:
        df = df.filter(pl.col("sza").ge(constants.MIN_SZA))
    if constants.MIN_XAIR is not None:
        df = df.filter(pl.col("XAIR").ge(constants.MIN_XAIR))
    if constants.MAX_XAIR is not None:
        df = df.filter(pl.col("XAIR").le(constants.MAX_XAIR))

    return df


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
    ils: Any = []
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


def load_vmr_file(results_folder: str, date: datetime.date, sensor_id: str) -> pd.DataFrame:
    # The content of the output VMR file is read separately for each
    # measurement day.
    # Each VMR file (i.e. VMR_fast_out.dat) contains:
    # 0: "Index", 1: "Altitude", 2: "H2O", 3: "HDO", 4: "CO2", 5: "CH4",
    # 6: "N2O", 7: "CO", 8: "O2", 9: "HF"
    names = ["Index", "Altitude", "H2O", "HDO", "CO2", "CH4", "N2O", "CO", "O2", "HF"]
    return pd.read_csv(
        os.path.join(
            results_folder,
            "raw_output_proffast",
            f"{sensor_id}{date.strftime('%y%m%d')}-VMR_fast_out.dat",
        ),
        header=None,
        skipinitialspace=True,
        usecols=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        names=names,
        sep=" ",
        engine="python",
    )


def load_pt_file(results_folder: str, date: datetime.date, sensor_id: str) -> pd.DataFrame:
    # The content of the pT output file is read separately for
    # each measurement day.
    # Each pT file (i.e. pT_fast_out.dat) contains:
    # 0: "Index", 1: "Altitude", 2: "Temperature", 3: "Pressure",
    # 4: "DryAirColumn", 5: "H2O", 6: "HDO"

    return pd.read_csv(
        os.path.join(
            results_folder,
            "raw_output_proffast",
            f"{sensor_id}{date.strftime('%y%m%d')}-VMR_fast_out.dat",
        ),
        header=0,
        skipinitialspace=True,
        usecols=[0, 1, 2, 3, 4, 5, 6],
        names=["Index", "Altitude", "Tem", "Pre", "DAC", "H2O", "HDO"],
        sep=" ",
        engine="python",
    )


def load_column_sensitivity_file(
    results_folder: str, date: datetime.date, sensor_id: str
) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any], np.ndarray[Any, Any], np.ndarray[Any, Any]]:
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

    day_str = date.strftime("%y%m%d")
    colsens_filename = f"{sensor_id}{date.strftime('%y%m%d')}-colsens.dat"
    path = os.path.join(results_folder, "raw_output_proffast", colsens_filename)

    # Read pressure and sensitivities as function of the altitude and SZA.

    with open(path, "r") as file:
        for i in range(8):  # H2O, HDO, CO2, CH4, N2O, CO, O2, HF
            sza.append([])
            alt.append([])
            pre.append([])
            sen.append([])

            for j in range(6):  # 6 header lines for each species
                header: Any = file.readline()  # skip header line
                if j == 3:  # read SZA [rad] values in the third line
                    header = re.sub(" +", "\t", header)
                    header = header.split("\t")  # tab separator
                    sza[i] = np.array(header[3:])  # SZA header/columns
                    sza[i] = sza[i].astype(float)  # string to float

            for j in range(49):  # number of altitude levels
                line: Any = file.readline()[1:-1]  # skip first empty
                # space and carriage return character at the end
                line = re.sub(" +", ",", line)  # replace empty spaces
                # by a comma
                line = line.split(",")  # split line into columns

                alt[i].append(line[0])  # altitude (first column)
                pre[i].append(line[1])  # pressure (second column)

                sen[i].append([])
                for k in range(2, len(line)):  # SZA (third column
                    # upwards, total 15 columns)
                    sen[i][j].append(float(line[k]))

    sza = np.array(sza, dtype=float)  # SZA [deg]
    alt = np.array(alt, dtype=float)  # altitude [km]
    pre = np.array(pre, dtype=float)  # pressure [mbar]
    sen = np.array(sen, dtype=float)  # sensitivity

    return sza, alt, pre, sen


def load_interpolated_column_sensitivity_file(
    results_folder: str,
    date: datetime.date,
    sensor_id: str,
    szas: np.ndarray[Any, Any],
) -> list[list[list[float]]]:
    sza, alt, pre, sen = load_column_sensitivity_file(results_folder, date, sensor_id)

    if (sza is None) or (alt is None) or (pre is None) or (sen is None):
        return None

    gas_sens: list[list[list[float]]] = []

    for k in range(8):  # H2O, HDO, CO2, CH4, N2O, CO, O2, HF
        gas_sens.append([])

        for i in range(len(szas)):
            # number of measurements

            gas_sens[k].append([])

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
                        gas_sens[k][i].append(gas_int)

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
                        gas_sens[k][i].append(gas_int)
    return gas_sens


def calculate_column_uncertainty(
    df: pl.DataFrame,
) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any], np.ndarray[Any, Any], np.ndarray[Any, Any]]:
    # The error calculation (uncertainty) is performed
    # by using the column mixing ratios and dry air mole fraction.

    XH2O = df["XH2O"].to_numpy()
    XCO2 = df["XCO2"].to_numpy()
    XCH4 = df["XCH4"].to_numpy()
    XCO = df["XCO"].to_numpy()

    AvgNr = 11  # number of moving mean values
    ErrNr = int(AvgNr / 2)  # number of moving mean values divided by two
    MeaNr = len(XH2O)  # number of measurements

    # Calculation of the moving mean for each species with 11 data points.

    XH2O_mean = np.zeros(df["JulianDate"].shape)
    XCO2_mean = np.zeros(df["JulianDate"].shape)
    XCH4_mean = np.zeros(df["JulianDate"].shape)
    XCO_mean = np.zeros(df["JulianDate"].shape)

    for i in range(MeaNr - AvgNr + 1):  # moving mean calculation
        XH2O_mean_tmp = 0.0
        XCO2_mean_tmp = 0.0
        XCH4_mean_tmp = 0.0
        XCO_mean_tmp = 0.0

        for j in range(AvgNr):
            XH2O_mean_tmp += XH2O[i + j]
            XCO2_mean_tmp += XCO2[i + j]
            XCH4_mean_tmp += XCH4[i + j]
            XCO_mean_tmp += XCO[i + j]

        XH2O_mean[i + ErrNr] = XH2O_mean_tmp / float(AvgNr)
        XCO2_mean[i + ErrNr] = XCO2_mean_tmp / float(AvgNr)
        XCH4_mean[i + ErrNr] = XCH4_mean_tmp / float(AvgNr)
        XCO_mean[i + ErrNr] = XCO_mean_tmp / float(AvgNr)

    for i in range(ErrNr):  # first entries const
        XH2O_mean[i] = XH2O_mean[ErrNr]
        XCO2_mean[i] = XCO2_mean[ErrNr]
        XCH4_mean[i] = XCH4_mean[ErrNr]
        XCO_mean[i] = XCO_mean[ErrNr]

    for i in range(ErrNr):  # last entries const
        XH2O_mean[MeaNr - i - 1] = XH2O_mean[MeaNr - ErrNr - 1]
        XCO2_mean[MeaNr - i - 1] = XCO2_mean[MeaNr - ErrNr - 1]
        XCH4_mean[MeaNr - i - 1] = XCH4_mean[MeaNr - ErrNr - 1]
        XCO_mean[MeaNr - i - 1] = XCO_mean[MeaNr - ErrNr - 1]

    # The error calculation is based on the difference between
    # the column mixing ratios
    # and the the moving mean value for each trace gas.
    # Therefore, it corresponds to a standard deviation with respect to
    # the moving mean.

    XH2O_err = np.zeros(MeaNr)
    XCO2_err = np.zeros(MeaNr)
    XCH4_err = np.zeros(MeaNr)
    XCO_err = np.zeros(MeaNr)

    for i in range(MeaNr - AvgNr + 1):
        XH2O_err_tmp = 0.0
        XCO2_err_tmp = 0.0
        XCH4_err_tmp = 0.0
        XCO_err_tmp = 0.0

        for j in range(AvgNr):
            XH2O_err_tmp += np.power(XH2O[i + j] - XH2O_mean[i + j], 2)
            XCO2_err_tmp += np.power(XCO2[i + j] - XCO2_mean[i + j], 2)
            XCH4_err_tmp += np.power(XCH4[i + j] - XCH4_mean[i + j], 2)
            XCO_err_tmp += np.power(XCO[i + j] - XCO_mean[i + j], 2)

        XH2O_err[i + ErrNr] = np.sqrt(XH2O_err_tmp / float(AvgNr - 1))
        XCO2_err[i + ErrNr] = np.sqrt(XCO2_err_tmp / float(AvgNr - 1))
        XCH4_err[i + ErrNr] = np.sqrt(XCH4_err_tmp / float(AvgNr - 1))
        XCO_err[i + ErrNr] = np.sqrt(XCO_err_tmp / float(AvgNr - 1)) * 1000.0

        if XH2O[i + ErrNr] == -900000.0:
            XH2O_err[i + ErrNr] = -900000.0
        if XCO2[i + ErrNr] == -900000.0:
            XCO2_err[i + ErrNr] = -900000.0
        if XCH4[i + ErrNr] == -900000.0:
            XCH4_err[i + ErrNr] = -900000.0
        if XCO[i + ErrNr] == -900000.0:
            XCO_err[i + ErrNr] = -900000.0

    # The uncertainty for the first and last entries is constant.

    for i in range(ErrNr):
        XH2O_err[i] = XH2O_err[ErrNr]
        XCO2_err[i] = XCO2_err[ErrNr]
        XCH4_err[i] = XCH4_err[ErrNr]
        XCO_err[i] = XCO_err[ErrNr]

        if XH2O[i] == -900000.0:
            XH2O_err[i] = -900000.0
        if XCO2[i] == -900000.0:
            XCO2_err[i] = -900000.0
        if XCH4[i] == -900000.0:
            XCH4_err[i] = -900000.0
        if XCO[i] == -900000.0:
            XCO_err[i] = -900000.0

    for i in range(ErrNr):
        XH2O_err[MeaNr - i - 1] = XH2O_err[MeaNr - ErrNr - 1]
        XCO2_err[MeaNr - i - 1] = XCO2_err[MeaNr - ErrNr - 1]
        XCH4_err[MeaNr - i - 1] = XCH4_err[MeaNr - ErrNr - 1]
        XCO_err[MeaNr - i - 1] = XCO_err[MeaNr - ErrNr - 1]

        if XH2O[MeaNr - i - 1] == -900000.0:
            XH2O_err[MeaNr - i - 1] = -900000.0
        if XCO2[MeaNr - i - 1] == -900000.0:
            XCO2_err[MeaNr - i - 1] = -900000.0
        if XCH4[MeaNr - i - 1] == -900000.0:
            XCH4_err[MeaNr - i - 1] = -900000.0
        if XCO[MeaNr - i - 1] == -900000.0:
            XCO_err[MeaNr - i - 1] = -900000.0

    return XH2O_err, XCO2_err, XCH4_err, XCO_err
