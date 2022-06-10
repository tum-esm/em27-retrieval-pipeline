import json
import os
import shutil
from src.utils import Logger, directories_are_equal
from src.utils.directory_utils import (
    assert_directory_list_equality,
    get_existing_src_directories,
)

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))


def run(config: dict, session):
    sensor = session["sensor"]
    date = str(session["date"])

    output_src = (
        f"{PROJECT_DIR}/outputs/{sensor}_"
        + f"SN{str(session['serial_number']).zfill(3)}_{date}_{date}"
    )
    output_csv = f"{output_src}/combined_invparms_{sensor}_{date}-{date}.csv"
    assert os.path.isdir(output_src), "pylot output directory missing"

    # --- MOVE OUTPUT DATA ---

    # determine output directory path on DSS
    day_was_successful = os.path.isfile(output_csv)
    if day_was_successful:
        with open(output_csv, "r") as f:
            day_was_successful = len(f.readlines()) > 1

    output_dst_success = config["dst"] + f"/{sensor}/proffast-outputs/{date}"
    output_dst_failed = config["dst"] + f"/{sensor}/proffast-outputs-failed/{date}"

    if day_was_successful:
        Logger.info(f"Retrieval was successful")
    else:
        Logger.info(f"Retrieval failed inside PROFFAST")

    # remove old outputs
    if os.path.isdir(output_dst_success):
        Logger.debug(f"Removing old successful output")
        shutil.rmtree(output_dst_success)
    if os.path.isdir(output_dst_failed):
        Logger.debug(f"Removing old failed output")
        shutil.rmtree(output_dst_failed)

    output_dst = output_dst_success if day_was_successful else output_dst_failed
    shutil.copytree(output_src, output_dst)
    shutil.rmtree(output_src)

    # --- MOVE INTERFEROGRAMS ---

    existing_src_directories = get_existing_src_directories(config, sensor, date)
    assert_directory_list_equality(existing_src_directories)

    ifg_src = existing_src_directories[0]
    ifg_dst = config["dst"] + f"/{sensor}/ifgs/{date}"
    if not os.path.isdir(ifg_dst):
        Logger.debug(f"Copying ifgs from {ifg_src} to dst")
        shutil.copytree(ifg_src, ifg_dst)

    ifg_src_upload = config["src"]["interferograms"]["upload"][sensor] + f"/{date}"
    if os.path.isdir(ifg_src_upload):
        # this check is actually unnecessary,
        # but I included it for safety reasons
        assert directories_are_equal(
            ifg_src_upload, ifg_dst
        ), "directories differ, skipped removal"
        Logger.debug("Removing ifgs from cloud")
        shutil.rmtree(ifg_src_upload)

    # --- POSSIBLY REMOVE ITEMS FROM MANUAL QUEUE ---

    with open(f"{PROJECT_DIR}/manual-queue.json", "r") as f:
        old_manual_queue_content = json.load(f)
    assert isinstance(old_manual_queue_content, list)

    new_manual_queue_content = list(
        filter(
            lambda x: not ((x["sensor"] == sensor) and (x["date"] == date)),
            old_manual_queue_content,
        )
    )
    if len(new_manual_queue_content) < len(old_manual_queue_content):
        Logger.debug("Removing item from manual queue")
        with open(f"{PROJECT_DIR}/manual-queue.json", "w") as f:
            json.dump(new_manual_queue_content, f, indent=4)
