import os
import shutil
from src import utils

PROJECT_DIR, CONFIG = utils.load_setup()

SRC = CONFIG["src"]["verticalProfiles"]
DST = f"{PROJECT_DIR}/inputs"


def run(session):
    sensor = str(session["sensor"])
    serial_number = str(session["serial_number"])
    date = str(session["date"])

    src_filepath = f"{SRC}/{sensor}{serial_number}/{sensor}{date}.map"
    dst_filepath = f"{DST}/{sensor}_map/{sensor}{date}.map"

    assert os.path.isfile(src_filepath), "Map file does not exist"

    shutil.copy(src_filepath, dst_filepath)
