from typing import Any
import datetime
import signal
from src import types, retrieval
from . import (
    move_log_files,
    move_profiles,
    move_ifg_files,
    move_outputs,
    update_templates,
    run_retrieval,
)


def run(config: types.Config, session: types.RetrievalSession, test_mode: bool = False) -> None:
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    logger = retrieval.utils.logger.Logger(
        container_id=session.ctn.container_id,
        # print_to_console=test_mode,
    )
    logger.info(f"Starting session in container id {session.ctn.container_id}")
    logger.info(
        f"Sensor {session.ctx.sensor_id}: "
        + f"from {session.ctx.from_datetime} to {session.ctx.to_datetime}"
    )
    logger.debug(f"Session object: {session.model_dump_json(indent=4)}")

    def _last_will() -> None:
        retrieval.utils.retrieval_status.RetrievalStatusList.update_item(
            session.retrieval_algorithm,
            session.atmospheric_profile_model,
            session.ctx.sensor_id,
            session.ctx.from_datetime,
            session.job_settings.output_suffix,
            process_end_time=datetime.datetime.now(tz=datetime.timezone.utc),
        )
        logger.archive()

    def _graceful_teardown(*args: Any) -> None:
        logger.info("Container was killed")
        _last_will()
        exit(0)

    signal.signal(signal.SIGINT, _graceful_teardown)
    signal.signal(signal.SIGTERM, _graceful_teardown)
    logger.info("Established graceful teardown hook")

    try:
        logger.debug("Moving atmospheric profiles")
        move_profiles.run(config, session)

        logger.debug("Moving ground pressure files")
        move_log_files.run(config, logger, session)

        logger.debug("Moving interferograms")
        valid_ifg_count = move_ifg_files.run(config, logger, session)
    except Exception as e:
        logger.warning(f"Inputs incomplete: {e}")
        _last_will()
        return

    if valid_ifg_count > 0:
        logger.info("Updating retrieval templates")
        try:
            update_templates.run(logger, session)
        except Exception as e:
            logger.exception(e, label="Failed to update templates")
            _last_will()
            return

        logger.info("Running proffast")
        try:
            run_retrieval.run(session, test_mode=test_mode)
            logger.debug("Pylot execution was successful")
        except Exception as e:
            logger.exception(e, label="Proffast execution failed")
    else:
        logger.info("Skipping proffast execution because there are no valid interferograms")

    # uncomment the following return if you want to observe the final
    # proffast outputs of one day in this working directory
    # return

    logger.info("Moving the outputs")
    try:
        move_outputs.run(config, logger, session, test_mode=test_mode)
        logger.info("Finished")
    except Exception as e:
        logger.exception(e, label="Moving outputs failed")

    _last_will()
