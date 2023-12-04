import os
import re
import subprocess
import tum_esm_utils
from src import types, retrieval


def run(
    config: types.Config,
    logger: retrieval.utils.logger.Logger,
    session: types.RetrievalSession,
) -> None:
    """Move interferogram files from the source directory to the input directory.

    Accepted file name pattern: `regex(^$(SENSORID)$(DATE).*\\.\\d+$)`

    Examples: `ma20201123.ifg.0001`, `ma20220316s0e00a.0001`"""

    assert config.retrieval is not None

    # FIND ALL FILENAMES OF INTERFEROGRAMS

    date_string = session.ctx.from_datetime.strftime("%Y%m%d")

    ifg_src_directory = os.path.join(
        config.general.data.interferograms.root,
        session.ctx.sensor_id,
        date_string,
    )
    expected_ifg_regex = config.retrieval.general.ifg_file_regex.replace(
        "$(SENSOR_ID)", session.ctx.sensor_id
    ).replace("$(DATE)", date_string)
    expected_ifg_pattern = re.compile(expected_ifg_regex)
    logger.debug(f"used regex for ifg files: {expected_ifg_regex}")

    ifg_filenames = list(
        sorted([
            f for f in os.listdir(ifg_src_directory)
            if expected_ifg_pattern.match(f) is not None
        ])
    )
    logger.debug(
        f"{len(ifg_filenames)} ifg files found in " +
        f"src directory ({ifg_src_directory})"
    )
    assert len(ifg_filenames) > 0, "no ifg input files"
    retrieval.utils.retrieval_status.RetrievalStatusList.update_item(
        session.ctx.sensor_id,
        session.ctx.from_datetime,
        ifg_count=len(ifg_filenames),
    )

    # (optional) MAKE INTERFEROGRAM FILES READ-ONLY

    if (config.retrieval.ifg_file_permissions.before_processing is not None):
        for f in ifg_filenames:
            try:
                tum_esm_utils.shell.change_file_permissions(
                    os.path.join(ifg_src_directory, f),
                    config.retrieval.ifg_file_permissions.before_processing,
                )
            except PermissionError:
                if config.retrieval.ifg_file_permissions.fail_on_permission_error:
                    raise
                else:
                    logger.warning(
                        f"failed to modify permissions of ifg file {f}"
                    )
    else:
        logger.debug(
            "skipping modification of ifg file permissions during processing"
        )

    # EXCLUDE CORRUPT INTERFEROGRAM FILES

    try:
        corrupt_filenames = list(
            tum_esm_utils.interferograms.detect_corrupt_ifgs(
                ifg_directory=ifg_src_directory
            ).keys()
        )
    except subprocess.CalledProcessError:
        raise AssertionError(
            "corrupt-files-detection has failed during execution"
        )

    logger.debug(
        f"Excluding {len(corrupt_filenames)} corrupt file(s) from retrieval" + (
            f" ({', '.join(corrupt_filenames)})" if len(corrupt_filenames) >
            0 else ""
        )
    )
    valid_ifg_filenames = [
        f for f in ifg_filenames if f not in corrupt_filenames
    ]

    # SYMLINK ALL VALID INTERFEROGRAM FILES AND
    # RENAME THEM TO THE FORMAT EXPECTED BY THE
    # PYLOT

    dst_date_path = os.path.join(
        session.ctn.data_input_path, "ifg", date_string[2 :]
    )
    os.mkdir(dst_date_path)
    for ifg_index, filename in enumerate(valid_ifg_filenames):
        os.symlink(
            os.path.join(ifg_src_directory, filename),
            os.path.join(dst_date_path, f"{date_string[2:]}SN.{ifg_index + 1}"),
        )
