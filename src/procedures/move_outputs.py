import json
import os
import shutil
from src.utils import (
    Logger,
    directories_are_equal,
    assert_directory_list_equality,
    get_existing_src_directories,
)

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))


def detect_error_type(output_src: str):
    if not os.path.isdir(f"{output_src}/logfiles"):
        return None

    known_errors: list[tuple[str, str]] = [
        ("preprocess_output", "charfilter not found!"),
        ("preprocess_output", "Zero IFG block size!"),
        ("inv_output", "CO channel: no natural grid!"),
    ]

    for o, m in known_errors:
        try:
            with open(f"{output_src}/logfiles/{o}.log", "r") as f:
                file_content = "".join(f.readlines())
            if m in file_content:
                return m
        except FileNotFoundError:
            pass

    return None


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
            if len(f.readlines()) > 1:
                Logger.debug(f"Retrieval output csv exists")
            else:
                day_was_successful = False
                Logger.warning(f"Retrieval output csv is empty")
    else:
        Logger.debug(f"Retrieval output csv is missing")

    output_dst_success = config["dst"] + f"/{sensor}/proffast-outputs/{date}"
    output_dst_failed = config["dst"] + f"/{sensor}/proffast-outputs-failed/{date}"

    if day_was_successful:
        output_dst = output_dst_success
    if not day_was_successful:
        output_dst = output_dst_failed
        error_type = detect_error_type(output_src)
        if error_type is None:
            Logger.debug("Unknown error type")
        else:
            Logger.debug(f"Known error type: {error_type}")

    # remove old outputs
    if os.path.isdir(output_dst_success):
        Logger.debug(f"Removing old successful output")
        shutil.rmtree(output_dst_success)
    if os.path.isdir(output_dst_failed):
        Logger.debug(f"Removing old failed output")
        shutil.rmtree(output_dst_failed)

    # move new outputs
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
