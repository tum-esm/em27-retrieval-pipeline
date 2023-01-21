import os
import shutil
from src import utils, custom_types

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))


def run(
    config: custom_types.Config,
    logger: utils.Logger,
    session: custom_types.Session,
) -> None:
    filename = f"datalogger-{session.sensor_id}-{session.date}.csv"
    src_filepath = os.path.join(
        config["src"]["datalogger"],
        session.sensor_id,
        filename,
    )
    dst_filepath = os.path.join(
        PROJECT_DIR,
        "inputs",
        session.container_id,
        f"{session.sensor_id}_pressure",
        filename,
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
