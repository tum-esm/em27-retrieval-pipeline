import os
import h5py
import tum_esm_utils
from src import types
from .utils import (
    load_comb_invparms_df,
    get_ils_form_preprocess_inp,
    load_pt_file,
    load_vmr_file,
    load_column_sensitivity_file,
    load_interpolated_column_sensitivity_file,
    calculate_column_uncertainty,
)


# TODO: apply calibration factors


class GEOMSWriter:
    @staticmethod
    def generate_geoms_file(results_folder: str) -> None:
        about = types.AboutRetrieval.model_validate_json(
            tum_esm_utils.files.load_json_file(os.path.join(results_folder, "about.json"))
        )
        sensor_id = about.session.ctx.sensor_id
        serial_number = about.session.ctx.serial_number
        from_dt, to_dt = about.session.ctx.from_datetime, about.session.ctx.to_datetime
        assert from_dt.date() == to_dt.date()
        label = from_dt.strftime("%Y%m%dT%H%M%S") + "-" + to_dt.strftime("%Y%m%dT%H%M%S")

        filename = f"geoms.groundbased_ftir.em27_tum_{sensor_id}_SN{serial_number:03d}_{label}.h5"
        filepath = os.path.join(results_folder, filename)
        hdf_file = h5py.File(filepath, "w")

        comb_invparms_df = load_comb_invparms_df(results_folder, sensor_id)

        pt_data = load_pt_file(results_folder, from_dt.date(), sensor_id)
        vmr_data = load_vmr_file(results_folder, from_dt.date(), sensor_id)
        ils_data = get_ils_form_preprocess_inp(results_folder, from_dt.date())
        column_sensitivity = load_column_sensitivity_file(results_folder, from_dt.date(), sensor_id)
        interpolated_column_sensitivity = load_interpolated_column_sensitivity_file(
            results_folder, from_dt.date(), sensor_id, comb_invparms_df["appSZA"].to_numpy()
        )
        XH2O_uncertainty, XCO2_uncertainty, XCH4_uncertainty, XCO_uncertainty = (
            calculate_column_uncertainty(comb_invparms_df)
        )
