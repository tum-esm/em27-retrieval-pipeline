from datetime import datetime
import json
import os
import shutil
import subprocess
from src.utils import (
    Logger,
    directories_are_equal,
    assert_directory_equality,
    get_existing_src_directories,
)
from src.utils.retrieval_queue import RetrievalQueue

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))


def detect_error_type(output_src: str):
    if not os.path.isdir(f"{output_src}/logfiles"):
        return None

    known_errors: list[tuple[str, str]] = [
        ("preprocess_output", "charfilter not found!"),
        ("preprocess_output", "Zero IFG block size!"),
        ("inv_output", "CO channel: no natural grid!"),
        ("inv_output", "Cannot access tabellated x-sections!"),
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

    output_dirname = {
        "2.0.1": "proffast-2.0-outputs",
        "2.1.1": "proffast-2.1-outputs",
    }[config["proffastVersion"]]
    output_dst = config["dst"] + f"/{sensor}/{output_dirname}"
    if not os.path.isdir(output_dst):
        os.mkdir(f"{output_dst}")
        os.mkdir(f"{output_dst}/successful")
        os.mkdir(f"{output_dst}/failed")

    output_dst_successful = f"{output_dst}/successful/{date}"
    output_dst_failed = f"{output_dst}/failed/{date}"

    if day_was_successful:
        output_dst = output_dst_successful
    if not day_was_successful:
        output_dst = output_dst_failed
        error_type = detect_error_type(output_src)
        if error_type is None:
            Logger.debug("Unknown error type")
        else:
            Logger.debug(f"Known error type: {error_type}")

    # remove old outputs
    if os.path.isdir(output_dst_successful):
        Logger.debug(f"Removing old successful output")
        shutil.rmtree(output_dst_successful)
    if os.path.isdir(output_dst_failed):
        Logger.debug(f"Removing old failed output")
        shutil.rmtree(output_dst_failed)

    # move new outputs
    shutil.copytree(output_src, output_dst)
    shutil.rmtree(output_src)

    # --- MOVE INTERFEROGRAMS ---

    existing_src_directories = get_existing_src_directories(config, sensor, date)
    assert_directory_equality(existing_src_directories)

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

    RetrievalQueue.remove_date_from_queue(sensor, date)

    # --- STORE AUTOMATION LOGS ---

    date_logs = Logger.get_date_logs()
    with open(f"{output_dst}/automation.log", "w") as f:
        f.writelines(date_logs)

    # --- STORE AUTOMATION INFO ---

    with open(f"{output_dst}/about.json", "w") as f:
        now = datetime.utcnow()
        commit_sha = (
            subprocess.check_output(
                ["git", "rev-parse", "--short", "--verify", "HEAD"], cwd=PROJECT_DIR
            )
            .decode()
            .replace("\n", "")
        )
        about_dict = {
            "proffastVersion": config["proffastVersion"],
            "locationRepository": config["locationRepository"],
            "automationVersion": commit_sha,
            "generationDate": now.strftime("%Y%m%d"),
            "generationTime": now.strftime("%T"),
        }
        json.dump(about_dict, f, indent=4)
