"""Write data into GEOMS compliant HDF5 files.

This code has been adapted from the PROFFASTpylot (https://doi.org/10.21105/joss.06481)
which is licensed under the GNU General Public License version 3. The authors of the
original code are Lena Feld, Benedikt Herkommer, Darko Dubravica affiliated with the
Karlsruhe Institut of Technology (KIT)."""

from typing import Literal, Optional
import datetime
import os
import re
import polars as pl
import numpy as np
import h5py
import tqdm
import tum_esm_utils
import sys

sys.path.append(tum_esm_utils.files.rel_to_abs_path("../../.."))

import src
from .utils import (
    load_comb_invparms_df,
    get_ils_form_preprocess_inp,
    load_pt_file,
    load_vmr_file,
    load_interpolated_column_sensitivity_file,
    calculate_column_uncertainty,
)
from .geoms_api import GEOMSAPI


# fmt: off
def generate_geoms_file(
    results_dir: str,
    geoms_metadata: src.types.GEOMSMetadata,
    calibration_factors: src.types.CalibrationFactorsList,
    geoms_config: src.types.GEOMSConfig,
    from_datetime: datetime.datetime,
    to_datetime: datetime.datetime,
) -> tuple[Optional[str], str]:
    """Generate a GEOMS file within a given results directory.
    
    Returns: filepath and status message."""
    
    about = src.types.AboutRetrieval.model_validate(
        tum_esm_utils.files.load_json_file(os.path.join(results_dir, "about.json")),
        context={"ignore-path-existence": True},
    )
    sensor_id = about.session.ctx.sensor_id
    location_id = about.session.ctx.location.location_id
    serial_number = about.session.ctx.serial_number
    from_dt, to_dt = about.session.ctx.from_datetime, about.session.ctx.to_datetime
    assert from_dt.date() == to_dt.date(), "Something is wrong"

    # determine calibration factors
    from_dt_calibration_factors_index = calibration_factors.get_index(sensor_id, from_dt)
    to_dt_calibration_factors_index = calibration_factors.get_index(sensor_id, to_dt)
    if from_dt_calibration_factors_index is None:
        raise ValueError(f"Calibration factors not found for {sensor_id} @ {from_dt}")
    if to_dt_calibration_factors_index is None:
        raise ValueError(f"Calibration factors not found for {sensor_id} @ {to_dt}")
    if from_dt_calibration_factors_index != to_dt_calibration_factors_index:
        raise ValueError(
            f"Calibration factors changed during the period {from_dt} - {to_dt}. "
            + "Please make sure, there is a break in the metadata setup timeseries"
        )

    # load dataframe
    pl_df = load_comb_invparms_df(results_dir, sensor_id, geoms_config)
    pl_df = pl_df.filter(
        (pl.col("utc") >= from_datetime) & (pl.col("utc") <= to_datetime)
    )
    if len(pl_df) < 11:
        return None, "Not enough data (less than 11 datapoints)"
    
    # determine filename
    data_from_dt: datetime.datetime = pl_df["utc"].min()  # type: ignore
    data_to_dt: datetime.datetime = pl_df["utc"].max()  # type: ignore
    geoms_location = geoms_metadata.locations[location_id]
    data_source = f"{geoms_metadata.general.network}_{geoms_metadata.general.affiliation}{serial_number:03d}"
    filename = (
        f"groundbased_{data_source}_{geoms_location}_"
        f"{data_from_dt.strftime('%Y%m%dT%H%M%SZ')}_"
        f"{data_to_dt.strftime('%Y%m%dT%H%M%SZ')}_"
        f"{geoms_metadata.data.file_version:03d}"
        f".h5"
    ).lower()
    tmp_filename = filename[:-2] + "tmp.h5"
    filepath = os.path.join(results_dir, filename)
    tmp_filepath = os.path.join(results_dir, tmp_filename)
    if os.path.isfile(tmp_filepath):
        os.remove(tmp_filepath)
    
    if os.path.isfile(filepath):
        if geoms_config.conflict_mode == "skip":
            return filepath, "File already exists"
        if geoms_config.conflict_mode == "error":
            raise FileExistsError(f"File already exists: {filepath}")
        os.remove(filepath)
    
    # apply calibration factors
    cal = calibration_factors.root[to_dt_calibration_factors_index]
    pl_df = pl_df.with_columns(
        pl.col("XCO2").mul(cal.xco2).alias("XCO2"),
        pl.col("XCH4").mul(cal.xch4).alias("XCH4"),
        pl.col("XH2O").mul(cal.xh2o).alias("XH2O"),
        pl.col("XCO").mul(cal.xco).alias("XCO"),
    )

    # load data inputs
    pt_df = load_pt_file(results_dir, from_dt.date(), sensor_id)
    vmr_df = load_vmr_file(results_dir, from_dt.date(), sensor_id)
    ils_data = get_ils_form_preprocess_inp(results_dir, from_dt.date())
    interpolated_column_sensitivity = load_interpolated_column_sensitivity_file(results_dir, from_dt.date(), sensor_id, pl_df["sza"].to_numpy())
    XH2O_uncertainty, XCO2_uncertainty, XCH4_uncertainty, XCO_uncertainty = calculate_column_uncertainty(pl_df)
    species_uncertainty = { "H2O": XH2O_uncertainty, "CO2": XCO2_uncertainty, "CH4": XCH4_uncertainty, "CO": XCO_uncertainty}
    
    # open hdf file, the writing functions only work with pandas (not polars)
    hdf_file = h5py.File(tmp_filepath, "w")
    df = pl_df.to_pandas()

    # setup
    GEOMSAPI.write_source(hdf_file)
    GEOMSAPI.write_datetime(hdf_file, df)
    GEOMSAPI.write_altitude(hdf_file, df, pt_df)
    GEOMSAPI.write_solar_angle_zenith(hdf_file, df)
    GEOMSAPI.write_solar_angle_azimuth(hdf_file, df)
    GEOMSAPI.write_instrument_latitude(hdf_file, df)
    GEOMSAPI.write_instrument_longitude(hdf_file, df)
    GEOMSAPI.write_instrument_altitude(hdf_file, df)

    # enclosure pressure sensor
    GEOMSAPI.write_surface_pressure(hdf_file, df)
    GEOMSAPI.write_surface_pressure_source(hdf_file, geoms_metadata, df)

    # pt profile
    GEOMSAPI.write_pressure(hdf_file, df, pt_df)
    GEOMSAPI.write_pressure_source(hdf_file, df)
    GEOMSAPI.write_temperature(hdf_file, df, pt_df)
    GEOMSAPI.write_temperature_source(hdf_file, df)

    # gases
    all_species: list[Literal["H2O", "CO2", "CH4", "CO"]] = ["H2O", "CO2", "CH4", "CO"]
    for species in all_species:
        GEOMSAPI.write_column(hdf_file, df, species)
        GEOMSAPI.write_column_uncertainty(hdf_file, species, species_uncertainty[species])
        GEOMSAPI.write_apriori(hdf_file, df, pt_df, vmr_df, species)
        GEOMSAPI.write_apriori_source(hdf_file, df, species, about.session.atmospheric_profile_model)
        GEOMSAPI.write_averaging_kernel(hdf_file, df, pt_df, interpolated_column_sensitivity, species)

    # air
    GEOMSAPI.write_air_partial(hdf_file, df, pt_df)
    GEOMSAPI.write_air_density(hdf_file, df, pt_df)
    GEOMSAPI.write_air_density_source(hdf_file, df)

    # metadata
    metadata = {
        # file
        "FILE_ACCESS":        geoms_metadata.file.access,
        "FILE_PROJECT_ID":   geoms_metadata.file.project_id,
        "FILE_DOI":          geoms_metadata.file.doi,
        "FILE_META_VERSION": geoms_metadata.file.meta_version,
        "FILE_NAME":         filename,
        
        # data
        "DATA_DISCIPLINE":   geoms_metadata.data.discipline,
        "DATA_GROUP":        geoms_metadata.data.group,
        "DATA_FILE_VERSION": f"{geoms_metadata.data.file_version:03d}",
        "DATA_QUALITY":      geoms_metadata.data.quality,
        "DATA_TEMPLATE":     geoms_metadata.data.template,
        "DATA_SOURCE":       data_source,
        "DATA_LOCATION":     geoms_location,
        "DATA_PROCESSOR":    f"PROFFAST Version {about.session.retrieval_algorithm.split('-')[-1]}",
        
        # contact
        "PI_NAME":        geoms_metadata.principle_investigator.name,
        "PI_EMAIL":       geoms_metadata.principle_investigator.email,
        "PI_AFFILIATION": geoms_metadata.principle_investigator.affiliation,
        "PI_ADDRESS":     geoms_metadata.principle_investigator.address,
        "DO_NAME":        geoms_metadata.data_originator.name,
        "DO_EMAIL":       geoms_metadata.data_originator.email,
        "DO_AFFILIATION": geoms_metadata.data_originator.affiliation,
        "DO_ADDRESS":     geoms_metadata.data_originator.address,
        "DS_NAME":        geoms_metadata.data_submitter.name,
        "DS_EMAIL":       geoms_metadata.data_submitter.email,
        "DS_AFFILIATION": geoms_metadata.data_submitter.affiliation,
        "DS_ADDRESS":     geoms_metadata.data_submitter.address
    }
    
    # write metadata
    
    variables: list[str] = hdf_file.keys()
    for key, value in metadata.items():
        hdf_file.attrs[key] = np.bytes_([value])
    hdf_file.attrs["DATA_VARIABLES"] = np.bytes_(";".join(variables))
    
    loc = about.session.ctx.location
    hdf_file.attrs["DATA_DESCRIPTION"] = np.bytes_((
        f"EM27/SUN (SN{serial_number:03d}) measurements from {loc.location_id} " +
        f"({loc.details}, {loc.lat} N {loc.lon} E {loc.alt} m)"
    ).encode("ascii", errors="ignore").decode("ascii"))
    hdf_file.attrs["DATA_MODIFICATIONS"] = np.bytes_(
        "ILS parms applied: "
        f"{str(ils_data)} (ME1, PE1, ME2, PE2). "
        "Calibration factors applied: "
        f"{cal.xco2} for XCO2, "
        f"{cal.xch4} for XCH4, "
        f"{cal.xh2o} for XH2O, "
        f"{cal.xco} for XCO."
    )

    hdf_file.attrs["DATA_START_DATE"] = np.bytes_(data_from_dt.strftime("%Y%m%dT%H%M%SZ"))
    hdf_file.attrs["DATA_STOP_DATE"] = np.bytes_(data_to_dt.strftime("%Y%m%dT%H%M%SZ"))
    hdf_file.attrs["FILE_GENERATION_DATE"] = np.bytes_(
        datetime.datetime.now().strftime("%Y%m%dT%H%M%SZ")
    )
    
    hdf_file.close()
    os.rename(tmp_filepath, filepath)
    return filepath, "File generated"

# fmt: on


def run() -> None:
    print("Loading configuration")
    config = src.types.Config.load()
    assert config.geoms is not None, "no geoms config found"

    print("Loading calibration factors")
    calibration_factors = src.types.CalibrationFactorsList.load()

    print("Loading geoms metadata")
    geoms_metadata = src.types.GEOMSMetadata.load()

    for retrieval_algorithm in config.geoms.retrieval_algorithms:
        for atmospheric_profile_model in config.geoms.atmospheric_profile_models:
            if (retrieval_algorithm == "proffast-1.0") and (atmospheric_profile_model == "GGG2020"):
                print("Skipping proffast-1.0/GGG2020 as it is not supported")
                continue

            print(f"Processing {retrieval_algorithm}/{atmospheric_profile_model}")

            for i, sensor_id in enumerate(config.geoms.sensor_ids):
                print(f"Processing sensor_id #{i + 1}")

                results_folders = os.path.join(
                    config.general.data.results.root,
                    retrieval_algorithm,
                    atmospheric_profile_model,
                    sensor_id,
                    "successful",
                )
                if not os.path.exists(results_folders):
                    print(f"Sensor {sensor_id}: no results found")
                    continue
                results = os.listdir(results_folders)
                results = [
                    result
                    for result in results
                    if os.path.isdir(os.path.join(results_folders, result))
                    and re.match(r"^\d{8}(_\d{8}_\d{8})?(_.+)?$", result)
                ]
                print(f"Sensor {sensor_id}: found {len(results)} results in total")
                results_within_time_range: list[str] = []
                for result in results:
                    date = datetime.datetime.strptime(result[:8], "%Y%m%d")
                    from_dt = datetime.datetime.combine(
                        date, datetime.time(0, 0, 0), tzinfo=datetime.timezone.utc
                    )
                    to_dt = datetime.datetime.combine(
                        date, datetime.time(23, 59, 59), tzinfo=datetime.timezone.utc
                    )
                    if len(result) > 8:
                        from_time = datetime.datetime.strptime(result.split("_")[1], "%H%M%S")
                        to_time = datetime.datetime.strptime(result.split("_")[2], "%H%M%S")
                        from_dt = from_dt.replace(
                            hour=from_time.hour, minute=from_time.minute, second=from_time.second
                        )
                        to_dt = to_dt.replace(
                            hour=to_time.hour, minute=to_time.minute, second=to_time.second
                        )

                    if (from_dt <= config.geoms.to_datetime) and (
                        to_dt >= config.geoms.from_datetime
                    ):
                        results_within_time_range.append(result)

                print(
                    f"Sensor {sensor_id}: found {len(results_within_time_range)} results within the time range"
                )

                progress = tqdm.tqdm(
                    sorted(results_within_time_range), dynamic_ncols=True, desc="..."
                )
                for result in progress:
                    progress.desc = f"{sensor_id}/{result}"
                    filepath, status_message = generate_geoms_file(
                        os.path.join(results_folders, result),
                        geoms_metadata,
                        calibration_factors,
                        config.geoms,
                        config.geoms.from_datetime,
                        config.geoms.to_datetime,
                    )
                    progress.write(
                        f"  {result}: {status_message}" + (f" ({filepath})" if filepath else "")
                    )


if __name__ == "__main__":
    geoms_metadata = src.types.GEOMSMetadata.load(template=True)
    calibration_factors = src.types.CalibrationFactorsList.load(template=True)
    geoms_config = src.types.Config.load(
        "/home/moritz-makowski/documents/em27/em27-retrieval-pipeline/config/config.template.json"
    ).geoms
    assert geoms_config is not None
    generate_geoms_file(
        results_dir="/data/01/retrieval-archive/v3/proffast-2.4/GGG2020/ma/successful/20241021",
        geoms_metadata=geoms_metadata,
        calibration_factors=calibration_factors,
        geoms_config=geoms_config,
        from_datetime=datetime.datetime(2024, 10, 20, 0, 0, 0),
        to_datetime=datetime.datetime(2024, 10, 23, 23, 59, 59),
    )
