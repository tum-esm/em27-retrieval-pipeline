import os
import h5py
import tum_esm_utils
import sys

sys.path.append(tum_esm_utils.files.rel_to_abs_path("../../.."))

from src import types
from utils import (
    load_comb_invparms_df,
    get_ils_form_preprocess_inp,
    load_pt_file,
    load_vmr_file,
    load_column_sensitivity_file,
    load_interpolated_column_sensitivity_file,
    calculate_column_uncertainty,
)
from geoms_api import GEOMSAPI


# TODO: apply calibration factors


class GEOMSWriter:
    @staticmethod
    def generate_geoms_file(results_folder: str) -> None:
        about = types.AboutRetrieval.model_validate(
            tum_esm_utils.files.load_json_file(os.path.join(results_folder, "about.json")),
            context={"ignore-path-existence": True},
        )
        sensor_id = about.session.ctx.sensor_id
        serial_number = about.session.ctx.serial_number
        from_dt, to_dt = about.session.ctx.from_datetime, about.session.ctx.to_datetime
        assert from_dt.date() == to_dt.date()
        label = from_dt.strftime("%Y%m%dT%H%M%S") + "-" + to_dt.strftime("%Y%m%dT%H%M%S")

        pl_df = load_comb_invparms_df(results_folder, sensor_id)
        if len(pl_df) < 11:
            print(f"Skipping this date because there are only {len(pl_df)} record")
            return

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

        # write file to results folder
        filename = f"geoms.groundbased_ftir.em27_tum_{sensor_id}_SN{serial_number:03d}_{label}.h5"
        filepath = os.path.join(results_folder, filename)
        hdf_file = h5py.File(filepath, "w")

        df = pl_df.to_pandas()

        # setup
        GEOMSAPI.write_datetime(hdf_file, df)
        GEOMSAPI.write_altitude(hdf_file, df, pt_df)
        GEOMSAPI.write_solar_angle_zenith(hdf_file, df)
        GEOMSAPI.write_solar_angle_azimuth(hdf_file, df)
        GEOMSAPI.write_instrument_latitude(hdf_file, df)
        GEOMSAPI.write_instrument_longitude(hdf_file, df)
        GEOMSAPI.write_instrument_altitude(hdf_file, df)

        # enclosure pressure sensor
        GEOMSAPI.write_surface_pressure(hdf_file, df)
        GEOMSAPI.write_surface_pressure_src(hdf_file, df, pressure_source_name="TODO")

        # pt profile
        GEOMSAPI.write_pressure(hdf_file, df, pt_df)
        GEOMSAPI.write_pressure_src(hdf_file, df)
        GEOMSAPI.write_temperature(hdf_file, df, pt_df)
        GEOMSAPI.write_temperature_src(hdf_file, df)

        # gases
        for species in ["H2O", "CO2", "CH4", "CO"]:
            GEOMSAPI.write_column(hdf_file, df, species)
            GEOMSAPI.write_column_uncertainty(hdf_file, df, species, species_uncertainty[species])
            GEOMSAPI.write_apriori(hdf_file, df, pt_df, vmr_df, species)
            GEOMSAPI.write_apriori_src(hdf_file, df, species, "GGG2020")
            GEOMSAPI.write_avk(hdf_file, df, pt_df, interpolated_column_sensitivity, species)

        # air
        GEOMSAPI.write_air_partial(hdf_file, df, pt_df)
        GEOMSAPI.write_air_density(hdf_file, df, pt_df)
        GEOMSAPI.write_air_density_src(hdf_file, df)


if __name__ == "__main__":
    GEOMSWriter.generate_geoms_file(
        "/data/01/retrieval-archive/v3/proffast-2.4/GGG2020/ma/successful/20241021"
    )
