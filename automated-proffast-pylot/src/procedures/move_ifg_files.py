import os
import shutil
import subprocess
from src import utils, types, detect_corrupt_ifgs

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
DST = f"{PROJECT_DIR}/inputs"


def run(config: types.ConfigDict, session: types.SessionDict) -> None:
    sensor, date = session["sensor"], session["date"]
    container_id = session["container_id"]

    existing_src_directories = utils.get_existing_src_directories(config, sensor, date)

    # no data for this sensor/date
    if len(existing_src_directories) == 0:
        utils.retrieval_queue.RetrievalQueue.remove_from_queue_file(
            sensor, date, config
        )
        raise AssertionError("No ifg directories found")

    if len(existing_src_directories) > 1:
        utils.assert_directory_equality(existing_src_directories)
        utils.Logger.debug(
            f"Found multiple ifgs directories (identical): {existing_src_directories}"
        )

    ifg_src = existing_src_directories[0]

    # Create empty output directory for that date
    dst_date_path = f"{DST}/{container_id}/{sensor}_ifg/{date[2:]}"
    os.mkdir(dst_date_path)

    copied_ifg_count = 0

    # move all valid ifg files and rename them properly
    file_count = len(os.listdir(ifg_src))
    utils.Logger.debug(f"{file_count} files/directories found in ifg src directory")
    for ifg_file in os.listdir(ifg_src):
        old_path = f"{ifg_src}/{ifg_file}"

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

    # remove corrupt_ifgs
    try:
        corrupt_files = list(detect_corrupt_ifgs.main.run(dst_date_path).keys())
    except subprocess.CalledProcessError:
        raise AssertionError("corrupt-files-detection has failed during execution")

    if len(corrupt_files) > 0:
        utils.Logger.debug(
            f"Removing {len(corrupt_files)} corrupt file(s): {corrupt_files}"
        )
        for f in corrupt_files:
            os.remove(f"{dst_date_path}/{f}")
    else:
        utils.Logger.debug(f"No corrupt files found")

    assert (
        copied_ifg_count > 0
    ), f"no ifgs in src directory, sourcing data from {ifg_src}"
