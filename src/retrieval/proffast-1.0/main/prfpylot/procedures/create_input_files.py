import datetime
import os
import pydantic
import tum_esm_utils
from src import custom_types
import polars as pl

_TEMPLATE_DIR = os.path.join(
    tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=2), "templates"
)
_ILS_PARAMS_PATH = os.path.join(
    tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=2),
    "ils-parameters.csv",
)


class ILSParams(pydantic.BaseModel):
    channel1_me: float
    channel1_pe: float
    channel2_me: float
    channel2_pe: float


def get_ils_params(serial_number: str, date: datetime.date) -> ILSParams:
    df = pl.read_csv(
        _ILS_PARAMS_PATH,
        columns=[
            "SERIAL_NUMBER",
            "CHANNEL1_ME",
            "CHANNEL1_PE",
            "CHANNEL2_ME",
            "CHANNEL2_PE",
            "VALID_SINCE",
        ],
        dtypes={
            "SERIAL_NUMBER": pl.Int16,
            "CHANNEL1_ME": pl.Float64,
            "CHANNEL1_PE": pl.Float64,
            "CHANNEL2_ME": pl.Float64,
            "CHANNEL2_PE": pl.Float64,
            "VALID_SINCE": pl.Date,
        },
    )

    df = df.filter(pl.col("SERIAL_NUMBER") == serial_number)
    df = df.filter(pl.col("VALID_SINCE") <= date)
    df = df.sort("VALID_SINCE", descending=True)
    df = df.head(1)

    return ILSParams(
        channel1_me=df["CHANNEL1_ME"][0],
        channel1_pe=df["CHANNEL1_PE"][0],
        channel2_me=df["CHANNEL2_ME"][0],
        channel2_pe=df["CHANNEL2_PE"][0],
    )


def _write_template_file(
    session: custom_types.ProffastSession,
    src_path: str,
    dst_path: str,
    additional_lines: list[str] = [],
) -> dict[str, str]:
    ils_params = get_ils_params(session.ctx.sensor_id, session.ctx.from_datetime.date())

    replacements = {
        "DATE": session.ctx.from_datetime.strftime("%Y%m%d"),
        "LOCATION_ID": session.ctx.location.location_id,
        "UTC_OFFSET": str(session.ctx.utc_offset),
        "SENSOR_ID": session.ctx.sensor_id,
        "LAT": str(session.ctx.location.lat),
        "LON": str(session.ctx.location.lon),
        "ALT": str(session.ctx.location.alt),
        "CHANNEL1_ME": str(ils_params.channel1_me),
        "CHANNEL1_PE": str(ils_params.channel1_pe),
        "CHANNEL2_ME": str(ils_params.channel2_me),
        "CHANNEL2_PE": str(ils_params.channel2_pe),
    }

    template_content = tum_esm_utils.files.load_file(src_path)
    file_content = (
        tum_esm_utils.text.insert_replacements(template_content, replacements).rstrip(
            "\n "
        )
        + "\n"
    )
    file_content += "\n".join(additional_lines)
    tum_esm_utils.files.dump_file(dst_path, file_content)


def create_preprocess_input_file(session: custom_types.ProffastSession) -> None:
    src_filepath = os.path.join(_TEMPLATE_DIR, "template_preprocess4.inp")
    dst_filepath = os.path.join(
        session.ctn.container_path, "prf", "preprocess", "preprocess4.inp"
    )
    date_string = session.ctx.from_datetime.strftime("%Y%m%d")
    ifg_dir = os.path.join(session.ctn.data_input_path, "ifg", date_string[2:])
    ifg_filepaths = [
        os.path.join(ifg_dir, f)
        for f in os.listdir(ifg_dir)
        if f.startswith(f"{date_string[2:]}SN.")
    ]
    _write_template_file(
        session,
        src_filepath,
        dst_filepath,
        additional_lines=[*ifg_filepaths, "***"],
    )


def create_pcxs_input_file(session: custom_types.ProffastSession) -> None:
    src_filepath = os.path.join(_TEMPLATE_DIR, "template_pcxs10.inp")
    dst_filepath = os.path.join(
        session.ctn.container_path, "prf", "inp_fast", "pcxs10.inp"
    )
    _write_template_file(session, src_filepath, dst_filepath, additional_lines=[])


def create_invers_input_file(session: custom_types.ProffastSession) -> None:
    src_filepath = os.path.join(_TEMPLATE_DIR, "template_invers10.inp")
    dst_filepath = os.path.join(
        session.ctn.container_path, "prf", "inp_fast", "invers10.inp"
    )
    date_string = session.ctx.from_datetime.strftime("%Y%m%d")
    spectra_dir = os.path.join(session.ctn.data_output_path, "analysis", date_string)
    spectra_filenames = [f for f in os.listdir(spectra_dir) if f.endswith(f"SN.BIN")]
    _write_template_file(
        session,
        src_filepath,
        dst_filepath,
        additional_lines=[*spectra_filenames, "***"],
    )
