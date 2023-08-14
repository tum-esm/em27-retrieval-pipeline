from datetime import datetime
import json
import os
import re
import shutil
from typing import Optional
import polars as pl
from src import utils, custom_types
import tum_esm_utils


def _detect_proffast22_error_type(output_src: str) -> Optional[str]:
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
    logger: utils.proffast.Logger,
    session: custom_types.ProffastSession,
) -> None:
    assert config.automated_proffast is not None

    date_string = session.ctx.from_datetime.strftime("%Y%m%d")

    if isinstance(session.ctn, custom_types.Proffast22Container):
        output_src_dir = (
            f"{session.ctn.data_output_path}/{session.ctx.sensor_id}_"
            + f"SN{str(session.ctx.serial_number).zfill(3)}_{date_string[2:]}-{date_string[2:]}"
        )
        output_csv_path = (
            f"{output_src_dir}/comb_invparms_{session.ctx.sensor_id}_"
            + f"SN{str(session.ctx.serial_number).zfill(3)}_"
            + f"{date_string[2:]}-{date_string[2:]}.csv"
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
            error_type = _detect_proffast22_error_type(output_src_dir)
            if error_type is None:
                logger.debug("Unknown error type")
            else:
                logger.debug(f"Known error type: {error_type}")
    else:
        output_src_dir = os.path.join(session.ctn.container_path, "prf", "out_fast")
        output_parquet_path = os.path.join(
            output_src_dir,
            f"{session.ctx.sensor_id}{date_string[2:]}-combined-invparms.parquet",
        )

        # DETERMINE WHETHER RETRIEVAL HAS BEEN SUCCESSFUL OR NOT

        day_was_successful = os.path.isfile(output_parquet_path)
        if day_was_successful:
            df = pl.read_parquet(output_parquet_path)
            if len(df) > 1:
                logger.debug(f"Retrieval output csv exists")
            else:
                day_was_successful = False
                logger.warning(f"Retrieval output csv exists but is empty")
        else:
            logger.debug(f"Retrieval output csv is missing")

    # DETERMINE OUTPUT DIRECTORY PATHS

    output_folder_slug = session.ctx.from_datetime.strftime("%Y%m%d")
    if session.ctx.multiple_ctx_on_this_date:
        output_folder_slug += session.ctx.from_datetime.strftime("_%H%M%S")
        output_folder_slug += session.ctx.to_datetime.strftime("_%H%M%S")

    output_dst_successful = os.path.join(
        config.general.data_dst_dirs.results,
        session.ctx.sensor_id,
        config.automated_proffast.general.retrieval_software + "-outputs",
        "successful",
        output_folder_slug,
    )
    output_dst_failed = os.path.join(
        config.general.data_dst_dirs.results,
        session.ctx.sensor_id,
        config.automated_proffast.general.retrieval_software + "-outputs",
        "failed",
        output_folder_slug,
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
    if isinstance(session.ctn, custom_types.Proffast22Container):
        shutil.copyfile(
            session.ctn.pylot_log_format_path,
            os.path.join(output_dst, "pylot_log_format.yml"),
        )

    # STORE AUTOMATION INFO

    with open(os.path.join(output_dst, "about.json"), "w") as f:
        now = datetime.utcnow()
        dumped_config = config.model_copy(deep=True)
        if dumped_config.general.location_data.access_token is not None:
            dumped_config.general.location_data.access_token = "REDACTED"

        about_dict = {
            "automationVersion": tum_esm_utils.shell.get_commit_sha(),
            "generationTime": now.strftime("%Y%m%dT%H:%M:%S+00:00"),
            "config": dumped_config.model_dump(),
            "session": session.model_dump(),
        }
        json.dump(about_dict, f, indent=4)

    # (optional) RESTORE OLD IFG FILE PERMISSIONS

    # TODO: make "failing if permission error" configurable
    if (
        config.automated_proffast.modified_ifg_file_permissions.after_processing
        is not None
    ):
        ifg_src_directory = os.path.join(
            config.general.data_src_dirs.interferograms,
            session.ctx.sensor_id,
            date_string,
        )
        expected_ifg_regex = config.automated_proffast.general.ifg_file_regex.replace(
            "$(SENSOR_ID)", session.ctx.sensor_id
        ).replace("$(DATE)", date_string)
        expected_ifg_pattern = re.compile(expected_ifg_regex)
        ifg_filenames = [
            filename
            for filename in os.listdir(ifg_src_directory)
            if expected_ifg_pattern.match(filename) is not None
        ]
        for filename in ifg_filenames:
            tum_esm_utils.shell.change_file_permissions(
                os.path.join(ifg_src_directory, filename),
                config.automated_proffast.modified_ifg_file_permissions.after_processing,
            )
        logger.debug(
            f"restored permissions for {len(ifg_filenames)} ifg "
            + f"files in src directory ({ifg_src_directory})"
        )
    else:
        logger.debug("skipping modification of ifg file permissions after processing")
