import os
import re
import shutil
import subprocess

import tum_esm_utils
from src import utils, custom_types


def run(
    config: custom_types.Config,
    logger: utils.Logger,
    session: custom_types.Session,
) -> None:
    # find all filenames of interferograms
    # possible file name patterns: ma20201123.ifg.0001, ma20220316s0e00a.0001
    ifg_src_directory = os.path.join(
        config.data_src_dirs.interferograms, session.sensor_id, session.date
    )
    expected_ifg_pattern = re.compile(r"^" + session.sensor_id + r"\d{8}.*\.\d+$")
    filenames = [
        f
        for f in os.listdir(ifg_src_directory)
        if expected_ifg_pattern.match(f) is not None
    ]
    logger.debug(
        f"{len(filenames)} files/directories found in ifg src directory ({ifg_src_directory})"
    )
    assert len(filenames) > 0, "no ifg input files"

    # Create empty output directory for that date
    dst_date_path = os.path.join(session.data_input_path, "ifg", session.date[2:])
    os.mkdir(dst_date_path)

    # move all valid ifg files and rename them properly
    for filename in filenames:
        ifg_number = filename.split(".")[-1]
        shutil.copy(
            os.path.join(ifg_src_directory, filename),
            os.path.join(dst_date_path, f"{session.date[2:]}SN.{ifg_number}"),
        )

    # remove corrupt_ifgs
    try:
        corrupt_filenames = list(
            tum_esm_utils.interferograms.detect_corrupt_ifgs(
                ifg_directory=dst_date_path
            ).keys()
        )
    except subprocess.CalledProcessError:
        raise AssertionError("corrupt-files-detection has failed during execution")

    if len(corrupt_filenames) > 0:
        logger.debug(
            f"Removing {len(corrupt_filenames)} corrupt file(s): {corrupt_filenames}"
        )
        for filename in corrupt_filenames:
            os.remove(os.path.join(dst_date_path, filename))
    else:
        logger.debug(f"No corrupt files found")
