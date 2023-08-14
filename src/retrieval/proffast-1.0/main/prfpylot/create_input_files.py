import datetime
import os
import shutil
import pydantic
import tum_esm_utils
from src import custom_types
import polars as pl

_PYLOT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__)
_TEMPLATE_DIR = os.path.join(_PYLOT_DIR, "templates")
_ILS_PARAMS_PATH = os.path.join(_PYLOT_DIR, "ils-parameters.csv")


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


def move_profiles_and_datalogger_files(session: custom_types.ProffastSession) -> None:
    analysis_path = os.path.join(session.ctn.data_output_path, "analysis")

    date_string = session.ctx.from_datetime.strftime("%Y%m%d")
    pt_path = os.path.join(analysis_path, f"{session.ctx.sensor_id}", date_string, "pT")
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
                f"datalogger-{session.ctx.sensor_id}-"
                + f"{session.ctx.from_datetime.strftime('%Y%m%d')}.csv"
            ),
        ),
        columns=["UTCtime___", "BaroYoung"],
        dtypes={"UTCtime___": str, "BaroYoung": float},
    )
    lines = [
        row["UTCtime___"] + "\t" + str(row["BaroYoung"])[:10] + "\t0.0"
        for row in df.iter_rows(named=True)
    ]
    file_content = template_content.rstrip("\n ") + "\n" + "\n".join(lines)
    tum_esm_utils.files.dump_file(
        os.path.join(pt_path, "pT_intraday.inp"), file_content
    )
