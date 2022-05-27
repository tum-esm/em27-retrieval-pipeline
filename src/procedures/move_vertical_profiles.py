import os
import shutil


dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
VERTICAL_PROFILES_DIR = (
    "/home/esm/fill-vertical-profiles-database/download-map-data/dataset"
)


def run(session):
    sensor = str(session["sensor"])
    serial_number = str(session["serial_number"])
    date = str(session["date"])

    src_filepath = f"{VERTICAL_PROFILES_DIR}/{sensor}{serial_number}/{sensor}{date}.map"
    dst_filepath = f"{PROJECT_DIR}/inputs/{sensor}_map/{sensor}{date}.map"

    assert os.path.isfile(src_filepath), "Map file does not exist"

    shutil.copy(src_filepath, dst_filepath)
