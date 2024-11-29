import json
import os
import subprocess

import tum_esm_utils

from src import retrieval, types, utils


def run(
    config: types.Config,
    logger: retrieval.utils.logger.Logger,
    session: types.RetrievalSession,
) -> int:
    """Move interferogram files from the source directory to the input directory.

    Accepted file name pattern: `regex(^$(SENSORID)$(DATE).*\\.\\d+$)`

    Examples: `ma20201123.ifg.0001`, `ma20220316s0e00a.0001`

    Returns the number of interferograms that passed the parser."""

    assert config.retrieval is not None

    # FIND ALL FILENAMES OF INTERFEROGRAMS

    ifg_src_directory = os.path.join(
        config.general.data.interferograms.root,
        session.ctx.sensor_id,
        session.ctx.from_datetime.strftime("%Y%m%d"),
    )
    _, ifg_file_pattern = utils.text.replace_regex_placeholders(
        config.retrieval.general.ifg_file_regex,
        session.ctx.sensor_id,
        session.ctx.from_datetime.date(),
    )
    logger.debug(f"used regex for ifg files: {ifg_file_pattern.pattern}")

    ifg_filenames = list(
        sorted([f for f in os.listdir(ifg_src_directory) if ifg_file_pattern.match(f) is not None])
    )
    logger.debug(
        f"{len(ifg_filenames)} ifg files found in " + f"src directory ({ifg_src_directory})"
    )
    assert len(ifg_filenames) > 0, "no ifg input files"
    retrieval.utils.retrieval_status.RetrievalStatusList.update_item(
        session.retrieval_algorithm,
        session.atmospheric_profile_model,
        session.ctx.sensor_id,
        session.ctx.from_datetime,
        session.job_settings.output_suffix,
        ifg_count=len(ifg_filenames),
    )

    # SYMLINK ALL VALID INTERFEROGRAM FILES AND
    # RENAME THEM TO THE FORMAT EXPECTED BY THE
    # PYLOT

    date_string = session.ctx.from_datetime.strftime("%Y%m%d")
    dst_date_path = os.path.join(session.ctn.data_input_path, "ifg", date_string[2:])
    os.mkdir(dst_date_path)
    for ifg_index, filename in enumerate(ifg_filenames):
        os.symlink(
            os.path.join(ifg_src_directory, filename),
            os.path.join(dst_date_path, f"{date_string[2:]}SN.{ifg_index + 1}"),
        )

    # OPTIONALLY EXCLUDE CORRUPT INTERFEROGRAM FILES

    if session.job_settings.use_ifg_corruption_filter:
        logger.info("Using ifg corruption filter")
        try:
            corruption_result = tum_esm_utils.em27.detect_corrupt_opus_files(
                ifg_directory=dst_date_path
            )
        except subprocess.CalledProcessError:
            raise AssertionError("corrupt-files-detection has failed during execution")

        if len(corruption_result) == 0:
            logger.info("No corrupt files found")
        else:
            logger.debug(
                f"Excluding {len(corruption_result)} corrupt file(s) from retrieval: "
                + json.dumps(corruption_result, indent=4)
            )
            for f in corruption_result.keys():
                os.remove(os.path.join(dst_date_path, f))

        if len(ifg_filenames) == len(corruption_result):
            raise AssertionError(
                "All interferograms are corrupt, no interferograms left for retrieval"
            )
        return len(ifg_filenames) - len(corruption_result)
    else:
        logger.info("Not using ifg corruption filter")
        return len(ifg_filenames)
