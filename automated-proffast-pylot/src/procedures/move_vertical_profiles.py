import os
import shutil
from src import custom_types

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))


def run(
    config: custom_types.Config,
    session: custom_types.Session,
) -> None:
    src_filepath = os.path.join(
        config.data_src_dirs.vertical_profiles,
        session.sensor_id,
        f"{session.sensor_id}{session.date}.map",
    )
    dst_filepath = os.path.join(
        session.pylot_container.data_input_path,
        "map",
        f"{session.sensor_id}{session.date}.map",
    )

    assert os.path.isfile(src_filepath), "map file does not exist"
    shutil.copy(src_filepath, dst_filepath)
