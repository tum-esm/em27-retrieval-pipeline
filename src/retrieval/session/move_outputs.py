import datetime
import os
import shutil

import tum_esm_utils

from src import retrieval, types, utils


def run(
    config: types.Config,
    logger: "retrieval.utils.logger.Logger",
    session: types.RetrievalSession,
    test_mode: bool = False,
) -> None:
    assert config.retrieval is not None

    date_string = session.ctx.from_datetime.strftime("%Y%m%d")
    output_src_dir: str
    day_was_successful: bool

    if isinstance(session, types.Proffast1RetrievalSession):
        output_src_dir = os.path.join(session.ctn.container_path, "prf", "out_fast")
        output_csv_path = os.path.join(
            output_src_dir,
            f"{session.ctx.sensor_id}{date_string[2:]}-combined-invparms.csv",
        )
    elif isinstance(session, types.Proffast2RetrievalSession):  # pyright: ignore[reportUnnecessaryIsInstance]
        output_src_dir = (
            f"{session.ctn.data_output_path}/{session.ctx.sensor_id}_"
            + f"SN{str(session.ctx.serial_number).zfill(3)}_{date_string[2:]}-{date_string[2:]}"
        )
        output_csv_path = (
            f"{output_src_dir}/comb_invparms_{session.ctx.sensor_id}_"
            + f"SN{str(session.ctx.serial_number).zfill(3)}_"
            + f"{date_string[2:]}-{date_string[2:]}.csv"
        )
    else:
        raise NotImplementedError(f"Retrieval session type {type(session)} not implemented")

    # DETERMINE WHETHER RETRIEVAL HAS BEEN SUCCESSFUL OR NOT
    day_was_successful = os.path.isfile(output_csv_path)
    if day_was_successful:
        with open(output_csv_path, "r") as f:
            if len(f.readlines()) > 1:
                logger.debug("Retrieval output csv exists")
            else:
                if not test_mode:
                    day_was_successful = False
                logger.warning("Retrieval output csv exists but is empty")
    else:
        logger.debug("Retrieval output csv is missing")

    # DETERMINE OUTPUT DIRECTORY PATHS
    output_slug = session.ctx.from_datetime.strftime("%Y%m%d")
    if not utils.functions.sdc_covers_the_full_day(session.ctx):
        output_slug += session.ctx.from_datetime.strftime("_%H%M%S")
        output_slug += session.ctx.to_datetime.strftime("_%H%M%S")
    if session.job_settings.output_suffix is not None:
        output_slug += f"_{session.job_settings.output_suffix}"

    output_dst = os.path.join(
        config.general.data.results.root,
        session.retrieval_algorithm,
        session.atmospheric_profile_model,
        session.ctx.sensor_id,
    )
    output_dst_successful = os.path.join(output_dst, "successful", output_slug)
    output_dst_failed = os.path.join(output_dst, "failed", output_slug)

    # REMOVE OLD OUTPUTS

    if os.path.isdir(output_dst_successful):
        logger.debug("Removing old successful output")
        shutil.rmtree(output_dst_successful)
    if os.path.isdir(output_dst_failed):
        logger.debug("Removing old failed output")
        shutil.rmtree(output_dst_failed)

    # CREATE EMPTY OUTPUT DIRECTORY

    output_dst = output_dst_successful if day_was_successful else output_dst_failed
    output_dst_tmp = output_dst + ".tmp"
    if os.path.isdir(output_dst_tmp):
        logger.debug("Removing old temporary output")
        shutil.rmtree(output_dst_tmp)

    # MOVE NEW OUTPUTS

    os.makedirs(os.path.dirname(output_dst_tmp), exist_ok=True)

    if os.path.isdir(output_src_dir):
        shutil.copytree(output_src_dir, output_dst_tmp)

        # STORE PT OUTPUT DIRECTORY

        analysis_dir: str
        if session.retrieval_algorithm == "proffast-1.0":
            analysis_dir = os.path.join(
                session.ctn.data_output_path,
                "analysis",
                session.ctx.sensor_id,
                session.ctx.from_datetime.strftime("%y%m%d"),
            )
        else:
            analysis_dir = os.path.join(
                session.ctn.data_output_path,
                "analysis",
                f"{session.ctx.sensor_id}_SN{session.ctx.serial_number:03d}",
                session.ctx.from_datetime.strftime("%y%m%d"),
            )

        os.makedirs(os.path.join(output_dst_tmp, "analysis"), exist_ok=True)
        if session.retrieval_algorithm == "proffast-1.0":
            shutil.copytree(
                os.path.join(analysis_dir, "pT"),
                os.path.join(output_dst_tmp, "analysis", "pT"),
            )
        else:
            shutil.copytree(
                os.path.join(session.ctn.container_path, "prf", "wrk_fast"),
                os.path.join(output_dst_tmp, "analysis", "pT"),
            )

        # (OPTIONAL) STORE BINARY SPECTRA

        if session.job_settings.store_binary_spectra:
            shutil.copytree(
                os.path.join(analysis_dir, "cal"),
                os.path.join(output_dst_tmp, "analysis", "cal"),
            )
        else:
            if session.retrieval_algorithm in [
                "proffast-2.2",
                "proffast-2.3",
                "proffast-2.4",
                "proffast-2.4.1",
            ]:
                os.makedirs(os.path.join(output_dst_tmp, "analysis", "cal"))
                shutil.copyfile(
                    os.path.join(analysis_dir, "cal", "logfile.dat"),
                    os.path.join(output_dst_tmp, "analysis", "cal", "logfile.dat"),
                )

        # STORE OPUS FILE STATS

        shutil.copyfile(
            os.path.join(session.ctn.container_path, "opus_file_stats.csv"),
            os.path.join(output_dst_tmp, "opus_file_stats.csv"),
        )

    # STORE AUTOMATION LOGS

    os.makedirs(os.path.join(output_dst_tmp, "logfiles"), exist_ok=True)
    shutil.copyfile(
        logger.logfile_path,
        os.path.join(output_dst_tmp, "logfiles", "container.log"),
    )
    if isinstance(session.ctn, types.Proffast22Container):
        shutil.copyfile(
            session.ctn.pylot_log_format_path,
            os.path.join(output_dst_tmp, "pylot_log_format.yml"),
        )

    # renamed with proffast pylot 2.4.1
    if os.path.isfile(os.path.join(output_dst_tmp, "proffastpylot_parameters.yml")):
        if os.path.isfile(os.path.join(output_dst_tmp, "pylot_config.yml")):
            os.remove(os.path.join(output_dst_tmp, "pylot_config.yml"))
        os.rename(
            os.path.join(output_dst_tmp, "proffastpylot_parameters.yml"),
            os.path.join(output_dst_tmp, "pylot_config.yml"),
        )

    # STORE AUTOMATION INFO

    with open(os.path.join(output_dst_tmp, "about.json"), "w") as f:
        now = datetime.datetime.now(datetime.timezone.utc)
        dumped_config = config.model_copy(deep=True)
        assert dumped_config.retrieval is not None
        if dumped_config.general.metadata is not None:
            if dumped_config.general.metadata.access_token is not None:
                dumped_config.general.metadata.access_token = "REDACTED"
        about = types.AboutRetrieval(
            automationVersion=utils.functions.get_pipeline_version(),
            automationCommitSha=tum_esm_utils.shell.get_commit_sha(),
            generationTime=now.strftime("%Y-%m-%dT%H:%M:%S%z"),
            config=types.AboutRetrievalConfig(
                general=dumped_config.general,
                retrieval=dumped_config.retrieval,
            ),
            session=session,
        )
        f.write(about.model_dump_json(indent=4))

    # RENAME TEMPORARY OUTPUT DIRECTORY

    # this operation is atomic, i.e., output directories
    # with a correct name are always complete
    os.rename(output_dst_tmp, output_dst)
