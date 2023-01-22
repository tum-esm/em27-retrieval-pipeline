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

    # TODO: move this line-count check into the merge-datalogger-files tool
    with open(src_filepath, "r") as f:
        line_count = len(f.readlines())

    # 1440 minutes per day + 1 header line
    if line_count < 1441:
        logger.warning(
            f"{session.sensor_id}/{session.date} - datalogger file only has {line_count}/1441 lines"
        )
    assert line_count >= 30, "datalogger file has less than 30 entries"

    # copy datalogger file
    shutil.copy(src_filepath, dst_filepath)
