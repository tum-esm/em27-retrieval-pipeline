import os
import shutil
from src import types

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))


def run(config: types.ConfigDict, session: types.SessionDict) -> None:
    sensor, date = session["sensor"], session["date"]

    src_filepath = os.path.join(
        config["src"]["vertical_profiles"], sensor, f"{sensor}{date}.map"
    )
    dst_filepath = os.path.join(
        PROJECT_DIR, "inputs", f"{sensor}_map", f"{sensor}{date}.map"
    )

    assert os.path.isfile(src_filepath), "map file does not exist"
    shutil.copy(src_filepath, dst_filepath)
