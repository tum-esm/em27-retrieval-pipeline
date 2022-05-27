import os
import shutil
from src import utils

PROJECT_DIR, CONFIG = utils.load_setup()


def run(session):
    sensor = session["sensor"]
    date = str(session["date"])

    map_src = f"{PROJECT_DIR}/inputs/{sensor}_map/{sensor}{date}.map"
    if os.path.isfile(map_src):
        os.remove(map_src)

    ifg_src = f"{PROJECT_DIR}/inputs/{sensor}_ifg/{date[2:]}"
    if os.path.isdir(ifg_src):
        shutil.rmtree(ifg_src)

    matching_pressure_files = list(
        filter(
            lambda f: f.startswith(f"{date[:4]}-{date[4:6]}-{date[6:]}_")
            and f.endswith(".dat"),
            os.listdir(f"{PROJECT_DIR}/inputs/{sensor}_pressure"),
        )
    )
    if len(matching_pressure_files) != 0:
        assert len(matching_pressure_files) == 1, "Multiple datalogger files found"
        os.remove(matching_pressure_files[0])
