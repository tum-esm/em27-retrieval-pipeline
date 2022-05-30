import os
import shutil
from src.utils import load_setup, Logger

PROJECT_DIR, CONFIG = load_setup()

SRC = CONFIG["src"]["interferograms"]
DST = f"{PROJECT_DIR}/inputs"


def run(session):
    sensor = session["sensor"]
    date = str(session["date"])

    src_date_path = f"{SRC}/{sensor}_ifg/{date}"
    assert os.path.isdir(src_date_path), "src path does not exist"

    # Create empty output directory for that date
    dst_date_path = f"{DST}/{sensor}_ifg/{date[2:]}"
    if os.path.isdir(dst_date_path):
        shutil.rmtree(dst_date_path)
    os.mkdir(dst_date_path)

    copied_ifg_count = 0

    # move all valid ifg files and rename them properly
    files = os.listdir(src_date_path)
    Logger.info(f"{sensor}/{date} - {len(files)} files found in ifg src directory")
    for ifg_file in os.listdir(src_date_path):
        old_path = f"{src_date_path}/{ifg_file}"

        # two possible filenames:
        # ma20201123.ifg.0001
        # ma20220316s0e00a.0001
        if all(
            [
                os.path.isfile(old_path),
                len(ifg_file.split(".")) >= 2,
                ifg_file.startswith(f"{sensor}{date}"),
                ifg_file.split(".")[-1].isnumeric(),
            ]
        ):
            ifg_number = ifg_file.split(".")[-1]
            shutil.copy(old_path, f"{dst_date_path}/{date[2:]}SN.{ifg_number}")
            copied_ifg_count += 1

    assert copied_ifg_count > 0, "no ifgs in src directory"
