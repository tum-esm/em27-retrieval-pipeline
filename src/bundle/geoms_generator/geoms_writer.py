import os
import h5py
import tum_esm_utils
from src import types
from .utils import load_comb_invparms_df, get_ils_form_preprocess_inp


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

        pt_filepath = os.path.join(
            results_folder,
            "raw_output_proffast",
            f"{sensor_id}{from_dt.date().strftime('%y%m%d')}-pT_fast_out.dat",
        )
        vmr_filepath = os.path.join(
            results_folder,
            "raw_output_proffast",
            f"{sensor_id}{from_dt.date().strftime('%y%m%d')}-VMR_fast_out.dat",
        )
        ils = get_ils_form_preprocess_inp(results_folder, from_dt.date())
