import os
import shutil
from src import custom_types, utils


def run(
    config: custom_types.Config,
    logger: utils.Logger,
    pylot_session: custom_types.PylotSession,
) -> None:
    src_filepath = os.path.join(
        config.data_src_dirs.datalogger,
        pylot_session.pressure_data_source,
        f"datalogger-{pylot_session.pressure_data_source}-{pylot_session.date}.csv",
    )
    dst_filepath = os.path.join(
        pylot_session.data_input_path,
        "log",
        f"datalogger-{pylot_session.pressure_data_source}-{pylot_session.date}.csv",
    )

    assert os.path.isfile(src_filepath), "no datalogger file found"
    with open(src_filepath) as f:
        log_file_line_count = f.read().count("\n") + 1

    # 1440 minutes per day + 1 header line
    if log_file_line_count < 1441:
        logger.warning(
            f"{pylot_session.sensor_id}/{pylot_session.date} - datalogger file only has {log_file_line_count}/1441 lines"
        )
    assert log_file_line_count >= 120, "datalogger file has less than 120 entries"

    # apply pressure calibration and save file
    shutil.copyfile(src_filepath, dst_filepath)
