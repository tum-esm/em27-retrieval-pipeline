import datetime
import json
import os
import shutil
import tum_esm_utils
import src
from src import retrieval


def run(
    config: src.types.Config,
    logger: retrieval.utils.logger.Logger,
    session: src.types.RetrievalSession,
    test_mode: bool = False,
) -> None:
    assert config.retrieval is not None

    date_string = session.ctx.from_datetime.strftime("%Y%m%d")
    output_src_dir: str
    day_was_successful: bool

    if isinstance(session, src.types.Proffast1RetrievalSession):
        output_src_dir = os.path.join(
            session.ctn.container_path, "prf", "out_fast"
        )
        output_csv_path = os.path.join(
            output_src_dir,
            f"{session.ctx.sensor_id}{date_string[2:]}-combined-invparms.csv",
        )
    elif isinstance(session, src.types.Proffast2RetrievalSession):
        output_src_dir = (
            f"{session.ctn.data_output_path}/{session.ctx.sensor_id}_" +
            f"SN{str(session.ctx.serial_number).zfill(3)}_{date_string[2:]}-{date_string[2:]}"
        )
        output_csv_path = (
            f"{output_src_dir}/comb_invparms_{session.ctx.sensor_id}_" +
            f"SN{str(session.ctx.serial_number).zfill(3)}_" +
            f"{date_string[2:]}-{date_string[2:]}.csv"
        )
    else:
        raise NotImplementedError(
            f"Retrieval session type {type(session)} not implemented"
        )

    assert os.path.isdir(output_src_dir), "retrieval output directory missing"

    # DETERMINE WHETHER RETRIEVAL HAS BEEN SUCCESSFUL OR NOT

    day_was_successful = os.path.isfile(output_csv_path)
    if day_was_successful:
        with open(output_csv_path, "r") as f:
            if len(f.readlines()) > 1:
                logger.debug(f"Retrieval output csv exists")
            else:
                if not test_mode:
                    day_was_successful = False
                logger.warning(f"Retrieval output csv exists but is empty")
    else:
        logger.debug(f"Retrieval output csv is missing")

    # DETERMINE OUTPUT DIRECTORY PATHS

    output_slug = session.ctx.from_datetime.strftime("%Y%m%d")
    if not src.utils.functions.sdc_covers_the_full_day(session.ctx):
        output_slug += session.ctx.from_datetime.strftime("_%H%M%S")
        output_slug += session.ctx.to_datetime.strftime("_%H%M%S")

    output_dst = os.path.join(
        config.general.data.results.root, session.retrieval_algorithm,
        session.atmospheric_profile_model, session.ctx.sensor_id
    )
    output_dst_successful = os.path.join(output_dst, "successful", output_slug)
    output_dst_failed = os.path.join(output_dst, "failed", output_slug)

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

    # (OPTIONAL) STORE BINARY SPECTRA

    if config.retrieval.general.store_binary_spectra:
        if isinstance(session, src.types.Proffast2RetrievalSession):
            shutil.copytree(
                os.path.join(
                    session.ctn.data_output_path, "analysis",
                    f"{session.ctx.sensor_id}_SN{session.ctx.serial_number:03d}",
                    session.ctx.from_datetime.strftime("%y%m%d"), "cal"
                ),
                os.path.join(output_dst, "binary_spectra"),
            )

    # STORE AUTOMATION LOGS

    os.makedirs(os.path.join(output_dst, "logfiles"), exist_ok=True)
    shutil.copyfile(
        logger.logfile_path,
        os.path.join(output_dst, "logfiles", "container.log"),
    )
    if isinstance(session.ctn, src.types.Proffast22Container):
        shutil.copyfile(
            session.ctn.pylot_log_format_path,
            os.path.join(output_dst, "pylot_log_format.yml"),
        )

    # STORE AUTOMATION INFO

    with open(os.path.join(output_dst, "about.json"), "w") as f:
        now = datetime.datetime.now(datetime.UTC)
        dumped_config = config.model_copy(deep=True)
        if dumped_config.general.metadata is not None:
            if dumped_config.general.metadata.access_token is not None:
                dumped_config.general.metadata.access_token = "REDACTED"

        assert dumped_config.retrieval is not None
        about_dict = {
            "automationVersion": tum_esm_utils.shell.get_commit_sha(),
            "generationTime": now.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "config": {
                "general": dumped_config.general.model_dump(mode="json"),
                "retrieval": dumped_config.retrieval.model_dump(mode="json"),
            },
            "session": session.model_dump(mode="json"),
        }
        json.dump(about_dict, f, indent=4)
