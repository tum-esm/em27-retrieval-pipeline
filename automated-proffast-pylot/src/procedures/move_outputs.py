from datetime import datetime
import json
import os
import shutil
from typing import Optional
from src import interfaces, utils, custom_types
import tum_esm_utils


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
    config: custom_types.Config,
    logger: utils.Logger,
    session: custom_types.Session,
) -> None:
    output_src_dir = (
        f"{session.data_output_path}/{session.sensor_id}_"
        + f"SN{str(session.serial_number).zfill(3)}_{session.date[2:]}-{session.date[2:]}"
    )
    output_csv_path = (
        f"{output_src_dir}/comb_invparms_{session.sensor_id}_"
        + f"SN{str(session.serial_number).zfill(3)}_"
        + f"{session.date[2:]}-{session.date[2:]}.csv"
    )
    assert os.path.isdir(output_src_dir), "pylot output directory missing"

    # DETERMINE WHETHER RETRIEVAL HAS BEEN SUCCESSFUL OR NOT

    day_was_successful = os.path.isfile(output_csv_path)
    if day_was_successful:
        with open(output_csv_path, "r") as f:
            if len(f.readlines()) > 1:
                logger.debug(f"Retrieval output csv exists")
            else:
                day_was_successful = False
                logger.warning(f"Retrieval output csv exists but is empty")
    else:
        logger.debug(f"Retrieval output csv is missing")
        error_type = detect_error_type(output_src_dir)
        if error_type is None:
            logger.debug("Unknown error type")
        else:
            logger.debug(f"Known error type: {error_type}")

    # DETERMINE OUTPUT DIRECTORY PATHS

    output_dst_successful = os.path.join(
        config.data_dst_dirs.results,
        session.sensor_id,
        "proffast-2.2-outputs",
        "successful",
        session.date,
    )
    output_dst_failed = os.path.join(
        config.data_dst_dirs.results,
        session.sensor_id,
        "proffast-2.2-outputs",
        "failed",
        session.date,
    )

    # REMOVE OLD OUTPUTS

    if os.path.isdir(output_dst_successful):
        logger.debug(f"Removing old successful output")
        shutil.rmtree(output_dst_successful)
    if os.path.isdir(output_dst_failed):
        logger.debug(f"Removing old failed output")
        shutil.rmtree(output_dst_failed)

    # CREATE EMPTY OUTPUT DIRECTORY

    output_dst = output_dst_successful if day_was_successful else output_dst_failed

    # MOVE NEW OUTPUTS

    os.makedirs(os.path.dirname(output_dst), exist_ok=True)
    shutil.copytree(output_src_dir, output_dst)
    shutil.rmtree(output_src_dir)

    # STORE AUTOMATION LOGS

    shutil.copyfile(
        logger.logfile_path,
        os.path.join(output_dst, "logfiles", "container.log"),
    )
    shutil.copyfile(
        session.pylot_log_format_path,
        os.path.join(output_dst, "pylot_log_format.yml"),
    )

    # POSSIBLY REMOVE ITEMS FROM MANUAL QUEUE

    interfaces.ManualQueueInterface.remove_item(session.sensor_id, session.date, logger)

    # STORE AUTOMATION INFO

    with open(os.path.join(output_dst, "about.json"), "w") as f:
        now = datetime.utcnow()
        about_dict = {
            "proffastVersion": "2.2",
            "automationVersion": tum_esm_utils.shell.get_commit_sha(),
            "generationDate": now.strftime("%Y%m%d"),
            "generationTime": now.strftime("%T"),
            "config": config.dict(),
            "session": session.dict(),
        }
        json.dump(about_dict, f, indent=4)
