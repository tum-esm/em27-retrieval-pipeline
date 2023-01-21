from datetime import datetime
import json
import os
import shutil
import subprocess
from typing import Optional
from src import utils, custom_types

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))


def detect_error_type(output_src: str) -> Optional[str]:
    if not os.path.isdir(f"{output_src}/logfiles"):
        return None

    known_errors: list[tuple[str, str]] = [
        ("preprocess_output.log", "charfilter not found!"),
        ("preprocess_output.log", "Zero IFG block size!"),
        ("inv_output.log", "CO channel: no natural grid!"),
        ("inv_output.log", "Cannot access tabellated x-sections!"),
    ]

    for logfile_name, message in known_errors:
        logfile_path = os.path.join(output_src, "logfiles", logfile_name)
        if os.path.isfile(logfile_path):
            with open(logfile_path) as f:
                file_content = "".join(f.readlines())
            if message in file_content:
                return message

    return None


def run(
    config: custom_types.ConfigDict,
    logger: utils.Logger,
    session: custom_types.SessionDict,
) -> None:
    sensor, date, container_id = (
        session["sensor"],
        session["date"],
        session["container_id"],
    )

    output_src = (
        f"{PROJECT_DIR}/outputs/{sensor}_"
        + f"SN{str(session['serial_number']).zfill(3)}_{date[2:]}-{date[2:]}"
    )
    output_csv = (
        f"{output_src}/comb_invparms_{sensor}_"
        + f"SN{str(session['serial_number']).zfill(3)}_"
        + f"{date[2:]}-{date[2:]}.csv"
    )
    assert os.path.isdir(output_src), "pylot output directory missing"

    # DETERMINE WHETHER RETRIEVAL HAS BEEN SUCCESSFUL OR NOT

    day_was_successful = os.path.isfile(output_csv)
    if day_was_successful:
        with open(output_csv, "r") as f:
            if len(f.readlines()) > 1:
                logger.debug(f"Retrieval output csv exists")
            else:
                day_was_successful = False
                logger.warning(f"Retrieval output csv exists but is empty")

        error_type = detect_error_type(output_src)
        if error_type is None:
            logger.debug("Unknown error type")
        else:
            logger.debug(f"Known error type: {error_type}")
    else:
        logger.debug(f"Retrieval output csv is missing")

    # DETERMINE OUTPUT DIRECTORY PATHS

    output_dst_successful = os.path.join(
        config.data_dst.results_dir,
        "proffast-2.2-outputs",
        sensor,
        "successful",
        date,
    )
    output_dst_failed = os.path.join(
        config.data_dst.results_dir,
        "proffast-2.2-outputs",
        sensor,
        "failed",
        date,
    )

    # REMOVE OLD OUTPUTS

    if os.path.isdir(output_dst_successful):
        logger.debug(f"Removing old successful output")
        shutil.rmtree(output_dst_successful)
    if os.path.isdir(output_dst_failed):
        logger.debug(f"Removing old failed output")
        shutil.rmtree(output_dst_failed)

    # CREATE EMPTY OUTPUT DIRECTORY

    if day_was_successful:
        output_dst = output_dst_successful
        os.makedirs(output_dst_successful, exist_ok=True)
    else:
        output_dst = output_dst_failed
        output_dst_failed = f"{output_dst}/failed/{date}"

    # MOVE NEW OUTPUTS

    shutil.copytree(output_src, output_dst)
    shutil.rmtree(output_src)

    # STORE AUTOMATION LOGS

    date_logs = logger.get_session_logs()
    with open(f"{output_dst}/automation_{container_id}.log", "w") as f:
        f.writelines(date_logs)

    # POSSIBLY REMOVE ITEMS FROM MANUAL QUEUE

    utils.RetrievalQueue.remove_from_queue_file(sensor, date, config, logger)

    # STORE AUTOMATION INFO

    with open(f"{output_dst}/about.json", "w") as f:
        now = datetime.utcnow()
        about_dict = {
            "proffastVersion": "2.2",
            "locationRepository": config.location_data.repository,
            "automationVersion": utils.get_commit_sha(),
            "generationDate": now.strftime("%Y%m%d"),
            "generationTime": now.strftime("%T"),
        }
        json.dump(about_dict, f, indent=4)

    # REMOVE SESSION CONTAINER

    # TODO: Remove session container
