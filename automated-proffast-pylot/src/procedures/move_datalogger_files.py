import os
import shutil
from src import utils, custom_types


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
    with open(src_filepath) as f:
        log_file_line_count = f.read().count("\n") + 1

    # 1440 minutes per day + 1 header line
    if log_file_line_count < 1441:
        logger.warning(
            f"{session.sensor_id}/{session.date} - datalogger file only has {log_file_line_count}/1441 lines"
        )
    assert log_file_line_count >= 120, "datalogger file has less than 120 entries"

    # apply pressure calibration and save file
    shutil.copyfile(src_filepath, dst_filepath)
