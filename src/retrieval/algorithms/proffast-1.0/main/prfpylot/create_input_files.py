from typing import Any
import os
import shutil
import tum_esm_utils
import polars as pl
from src import types, retrieval

_PYLOT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__)
_TEMPLATE_DIR = os.path.join(_PYLOT_DIR, "templates")


def _write_template_file(
    session: types.RetrievalSession,
    src_path: str,
    dst_path: str,
    additional_lines: list[str] = [],
) -> None:
    ils_params = retrieval.utils.ils.get_ils_params(
        session.ctx.serial_number, session.ctx.from_datetime.date()
    )

    replacements = {
        "DATE8": session.ctx.from_datetime.strftime("%Y%m%d"),
        "DATE6": session.ctx.from_datetime.strftime("%Y%m%d")[2 :],
        "LOCATION_ID": session.ctx.location.location_id,
        "UTC_OFFSET": str(session.ctx.utc_offset),
        "SENSOR_ID": session.ctx.sensor_id,
        "CONTAINER_PATH": session.ctn.container_path,
        "LAT": str(session.ctx.location.lat),
        "LON": str(session.ctx.location.lon),
        "ALT": str(session.ctx.location.alt / 1000),
        "CHANNEL1_ME": str(ils_params.channel1_me),
        "CHANNEL1_PE": str(ils_params.channel1_pe),
        "CHANNEL2_ME": str(ils_params.channel2_me),
        "CHANNEL2_PE": str(ils_params.channel2_pe),
    }

    template_content = tum_esm_utils.files.load_file(src_path)
    file_content = (
        tum_esm_utils.text.insert_replacements(template_content, replacements).rstrip("\n ") + "\n"
    )
    file_content += "\n".join(additional_lines)
    tum_esm_utils.files.dump_file(dst_path, file_content)


def create_preprocess_input_file(session: types.RetrievalSession) -> None:
    src_filepath = os.path.join(_TEMPLATE_DIR, "template_preprocess4.inp")
    dst_filepath = os.path.join(session.ctn.container_path, "prf", "preprocess", "preprocess4.inp")
    date_string = session.ctx.from_datetime.strftime("%Y%m%d")
    ifg_dir = os.path.join(session.ctn.data_input_path, "ifg", date_string[2 :])
    ifg_filepaths = [
        os.path.join(ifg_dir, f)
        for f in os.listdir(ifg_dir) if f.startswith(f"{date_string[2:]}SN.")
    ]
    os.mkdir(os.path.join(session.ctn.data_input_path, "ifg", date_string[2 :], "cal"))
    _write_template_file(
        session,
        src_filepath,
        dst_filepath,
        additional_lines=[*ifg_filepaths, "***"],
    )


def create_pcxs_input_file(session: types.RetrievalSession) -> None:
    src_filepath = os.path.join(_TEMPLATE_DIR, "template_pcxs10.inp")
    dst_filepath = os.path.join(session.ctn.container_path, "prf", "inp_fast", "pcxs10.inp")
    _write_template_file(session, src_filepath, dst_filepath, additional_lines=[])


def create_invers_input_file(session: types.RetrievalSession) -> None:
    src_filepath = os.path.join(_TEMPLATE_DIR, "template_invers10.inp")
    dst_filepath = os.path.join(session.ctn.container_path, "prf", "inp_fast", "invers10.inp")
    date_string = session.ctx.from_datetime.strftime("%Y%m%d")
    spectra_dir = os.path.join(
        session.ctn.data_output_path,
        "analysis",
        session.ctx.sensor_id,
        date_string[2 :],
        "cal",
    )
    spectra_filenames = [f for f in os.listdir(spectra_dir) if f.endswith("SN.BIN")]
    _write_template_file(
        session,
        src_filepath,
        dst_filepath,
        additional_lines=[*spectra_filenames, "***"],
    )


def move_profiles_and_ground_pressure_files(session: types.RetrievalSession) -> None:
    analysis_path = os.path.join(session.ctn.data_output_path, "analysis")

    date_string = session.ctx.from_datetime.strftime("%Y%m%d")
    pt_path = os.path.join(analysis_path, f"{session.ctx.sensor_id}", date_string[2 :], "pT")
    os.makedirs(pt_path, exist_ok=True)

    # copy atmospheric profile
    profile_filename = f"{session.ctx.sensor_id}{date_string}.map"
    profile_src = os.path.join(session.ctn.data_input_path, "map", profile_filename)
    profile_dst = os.path.join(pt_path, profile_filename)
    shutil.copyfile(profile_src, profile_dst)

    # write pT_intraday.inp file
    template_content = tum_esm_utils.files.load_file(
        os.path.join(_TEMPLATE_DIR, "template_pT_intraday.inp")
    )
    df = pl.read_csv(
        os.path.join(
            session.ctn.data_input_path,
            "log",
            (
                f"ground-pressure-{session.ctx.pressure_data_source}-" +
                f"{session.ctx.from_datetime.strftime('%Y%m%d')}.csv"
            ),
        ),
        columns=["utc-time", "pressure"],
    )

    def row_to_str(row: dict[str, Any]) -> str:
        time = str(row["utc-time"]).replace(":", "")
        pressure = float(row["pressure"])
        return f"{time}\t{pressure:.1f}\t0.0"

    lines = [row_to_str(row) for row in df.iter_rows(named=True)]
    file_content = template_content.rstrip("\n ") + "\n" + "\n".join(lines) + "\n***"
    tum_esm_utils.files.dump_file(os.path.join(pt_path, "pT_intraday.inp"), file_content)
