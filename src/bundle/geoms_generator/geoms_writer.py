import datetime
import os
import h5py
import numpy as np
import tum_esm_utils
import sys

sys.path.append(tum_esm_utils.files.rel_to_abs_path("../../.."))

from src import types
from utils import (
    load_comb_invparms_df,
    get_ils_form_preprocess_inp,
    load_pt_file,
    load_vmr_file,
    load_interpolated_column_sensitivity_file,
    calculate_column_uncertainty,
)
from geoms_api import GEOMSAPI
import constants


# TODO: apply calibration factors


class GEOMSWriter:
    @staticmethod
    def generate_geoms_file(results_folder: str) -> None:
        about = types.AboutRetrieval.model_validate(
            tum_esm_utils.files.load_json_file(os.path.join(results_folder, "about.json")),
            context={"ignore-path-existence": True},
        )
        sensor_id = about.session.ctx.sensor_id
        location_id = about.session.ctx.location.location_id
        serial_number = about.session.ctx.serial_number
        from_dt, to_dt = about.session.ctx.from_datetime, about.session.ctx.to_datetime
        assert from_dt.date() == to_dt.date()

        pl_df = load_comb_invparms_df(results_folder, sensor_id)
        if len(pl_df) < 11:
            print(f"Skipping this date because there are only {len(pl_df)} record")
            return

        data_from_dt = pl_df["utc"].min()
        data_to_dt = pl_df["utc"].max()

        pt_df = load_pt_file(results_folder, from_dt.date(), sensor_id)
        vmr_df = load_vmr_file(results_folder, from_dt.date(), sensor_id)
        ils_data = get_ils_form_preprocess_inp(results_folder, from_dt.date())
        interpolated_column_sensitivity = load_interpolated_column_sensitivity_file(
            results_folder, from_dt.date(), sensor_id, pl_df["sza"].to_numpy()
        )
        XH2O_uncertainty, XCO2_uncertainty, XCH4_uncertainty, XCO_uncertainty = (
            calculate_column_uncertainty(pl_df)
        )
        species_uncertainty = {
            "H2O": XH2O_uncertainty,
            "CO2": XCO2_uncertainty,
            "CH4": XCH4_uncertainty,
            "CO": XCO_uncertainty,
        }
        evdc_location = constants.EVDC_LOCATIONS[location_id]
        data_source = f"{constants.EVDC_NETWORK}_{constants.EVDC_AFFILIATION}{serial_number:03d}"
        filename = (
            f"groundbased_{data_source}_{evdc_location}_"
            f"{data_from_dt.strftime('%Y%m%dT%H%M%SZ')}_"
            f"{data_to_dt.strftime('%Y%m%dT%H%M%SZ')}_"
            f"{constants.EVDC_METADATA['DATA_FILE_VERSION']}"
            f".h5"
        ).lower()
        filepath = os.path.join(results_folder, filename)
        hdf_file = h5py.File(filepath, "w")

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
        GEOMSAPI.write_surface_pressure_source(hdf_file, df, pressure_source_name="TODO")

        # pt profile
        GEOMSAPI.write_pressure(hdf_file, df, pt_df)
        GEOMSAPI.write_pressure_source(hdf_file, df)
        GEOMSAPI.write_temperature(hdf_file, df, pt_df)
        GEOMSAPI.write_temperature_source(hdf_file, df)

        # gases
        for species in ["H2O", "CO2", "CH4", "CO"]:
            GEOMSAPI.write_column(hdf_file, df, species)
            GEOMSAPI.write_column_uncertainty(hdf_file, df, species, species_uncertainty[species])
            GEOMSAPI.write_apriori(hdf_file, df, pt_df, vmr_df, species)
            GEOMSAPI.write_apriori_source(hdf_file, df, species, "GGG2020")
            GEOMSAPI.write_averaging_kernel(
                hdf_file, df, pt_df, interpolated_column_sensitivity, species
            )

        # air
        GEOMSAPI.write_air_partial(hdf_file, df, pt_df)
        GEOMSAPI.write_air_density(hdf_file, df, pt_df)
        GEOMSAPI.write_air_density_source(hdf_file, df)

        # metadata
        metadata = {**constants.EVDC_METADATA}
        metadata["DATA_SOURCE"] = data_source
        metadata["DATA_LOCATION"] = evdc_location
        metadata["FILE_NAME"] = filename
        GEOMSWriter.write_metadata(
            hdf_file,
            serial_number,
            ils_data,
            calibration_factors={"XCO2": 1.0, "XCH4": 1.0, "XH2O": 1.0, "XCO": 1.0},
            data_from_dt=data_from_dt,
            data_to_dt=data_to_dt,
            metadata=metadata,
        )

    @staticmethod
    def write_metadata(
        hdf5_file: h5py.File,
        serial_number: int,
        ils_parameters: tuple[float, float, float, float],
        calibration_factors: dict[str, float],
        data_from_dt: datetime.datetime,
        data_to_dt: datetime.datetime,
        metadata: dict[str, str],
    ) -> None:
        """Write metadata to the GEOMS file!"""

        variables: list[str] = hdf5_file.keys()
        for key, value in metadata.items():
            hdf5_file.attrs[key] = np.bytes_([value])

        hdf5_file.attrs["DATA_DESCRIPTION"] = np.bytes_(
            f"EM27/SUN ({serial_number}) measurements from {constants.SITE_DESCRIPTION}."
        )
        hdf5_file.attrs["DATA_MODIFICATIONS"] = np.bytes_(
            "ILS parms applied: "
            f"{str(ils_parameters)} (ME1, PE1, ME2, PE2). "
            "Calibration factors applied: "
            f"{calibration_factors['XCO2']} for XCO2, "
            f"{calibration_factors['XCH4']} for XCH4, "
            f"{calibration_factors['XH2O']} for XH2O, "
            f"{calibration_factors['XCO']} for XCO."
        )

        hdf5_file.attrs["DATA_START_DATE"] = np.bytes_(data_from_dt.strftime("%Y%m%dT%H%M%SZ"))
        hdf5_file.attrs["DATA_STOP_DATE"] = np.bytes_(data_to_dt.strftime("%Y%m%dT%H%M%SZ"))
        hdf5_file.attrs["DATA_VARIABLES"] = np.bytes_(";".join(variables))
        hdf5_file.attrs["FILE_GENERATION_DATE"] = np.bytes_(
            datetime.datetime.now().strftime("%Y%m%dT%H%M%SZ")
        )


if __name__ == "__main__":
    GEOMSWriter.generate_geoms_file(
        "/data/01/retrieval-archive/v3/proffast-2.4/GGG2020/ma/successful/20241021"
    )
