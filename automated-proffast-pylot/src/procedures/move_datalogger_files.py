import os
import polars as pl
from src import utils, custom_types


def load_datalogger_df(path: str) -> pl.DataFrame:
    df = pl.read_csv(
        path,
        has_header=True,
        columns=[
            "UTCtime___",
            "BaroTHB40",
            "BaroYoung",
            "GPSAlt",
            "GPSLat",
            "GPSLong",
            "GPSTDiff",
            "GPShdop",
            "HygroTHB40",
            "ThermoTHB40",
            "UTCdate_____",
            "UTCsec____",
        ],
    )
    return df


def run(
    config: custom_types.Config,
    logger: utils.Logger,
    session: custom_types.Session,
) -> None:
    src_filepath = os.path.join(
        config.data_src_dirs.datalogger,
        session.sensor_id,
        f"datalogger-{session.sensor_id}-{session.date}.csv",
    )
    dst_filepath = os.path.join(
        session.data_input_path,
        "log",
        f"datalogger-{session.sensor_id}-{session.date}.csv",
    )

    assert os.path.isfile(src_filepath), "no datalogger file found"
    raw_df = load_datalogger_df(src_filepath)

    # 1440 minutes per day + 1 header line
    if len(raw_df) < 1441:
        logger.warning(
            f"{session.sensor_id}/{session.date} - datalogger file only has {len(raw_df)}/1441 lines"
        )
    assert len(raw_df) >= 120, "datalogger file has less than 120 entries"

    # apply pressure calibration and save file
    calibrated_df = raw_df.with_columns(
        pl.col("BaroYoung") * session.pressure_calibration_factor
    )
    calibrated_df.write_csv(dst_filepath, null_value="NaN")
