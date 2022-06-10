import os
import shutil

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))


def run(config: dict, session):
    SRC = config["src"]["verticalProfiles"]
    DST = f"{PROJECT_DIR}/inputs"

    sensor = str(session["sensor"])
    serial_number = str(session["serial_number"])
    date = str(session["date"])

    src_filepath = f"{SRC}/{sensor}{serial_number}/{sensor}{date}.map"
    dst_filepath = f"{DST}/{sensor}_map/{sensor}{date}.map"

    assert os.path.isfile(src_filepath), "map file does not exist"
    shutil.copy(src_filepath, dst_filepath)
