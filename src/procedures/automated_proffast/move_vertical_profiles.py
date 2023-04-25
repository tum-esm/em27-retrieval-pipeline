import os
import shutil
from src import custom_types


def run(
    config: custom_types.Config,
    pylot_session: custom_types.PylotSession,
) -> None:
    src_filepath = os.path.join(
        config.general.data_src_dirs.vertical_profiles,
        "GGG2014",
        pylot_session.sensor_id,
        f"{pylot_session.sensor_id}{pylot_session.date}.map",
    )
    dst_filepath = os.path.join(
        pylot_session.data_input_path,
        "map",
        f"{pylot_session.sensor_id}{pylot_session.date}.map",
    )

    assert os.path.isfile(src_filepath), "map file does not exist"
    shutil.copy(src_filepath, dst_filepath)
