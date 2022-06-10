import os
import shutil
from src.utils import (
    Logger,
    get_existing_src_directories,
    assert_directory_list_equality,
)

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
DST = f"{PROJECT_DIR}/inputs"


def run(config: dict, session):
    sensor = session["sensor"]
    date = str(session["date"])

    existing_src_directories = get_existing_src_directories(config, sensor, date)
    assert_directory_list_equality(existing_src_directories)

    assert len(existing_src_directories) > 0, "No ifg directories found"
    if len(existing_src_directories) > 1:
        Logger.debug(
            f"Found multiple ifgs directories (identical): {existing_src_directories}"
        )

    ifg_src = existing_src_directories[0]

    # Create empty output directory for that date
    dst_date_path = f"{DST}/{sensor}_ifg/{date[2:]}"
    os.mkdir(dst_date_path)

    copied_ifg_count = 0

    # move all valid ifg files and rename them properly
    file_count = len(os.listdir(ifg_src))
    Logger.info(f"{file_count} files/directories found in ifg src directory")
    for ifg_file in os.listdir(ifg_src):
        old_path = f"{ifg_src}/{ifg_file}"

        # TODO: Possibly include our own mechanism of detecting corrupt ifgs

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
