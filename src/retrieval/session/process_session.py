from typing import Any
import datetime
import signal
import src
from src import retrieval
from . import (
    move_log_files,
    move_profiles,
    move_ifg_files,
    move_outputs,
    run_retrieval,
)


def run(
    config: src.types.Config,
    session: src.types.RetrievalSession,
    test_mode: bool = False
) -> None:
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    logger = retrieval.utils.logger.Logger(
        container_id=session.ctn.container_id,
        # print_to_console=test_mode,
    )
    logger.info(f"Starting session in container id {session.ctn.container_id}")
    logger.info(
        f"Sensor {session.ctx.sensor_id}: " +
        f"from {session.ctx.from_datetime} to {session.ctx.to_datetime}"
    )
    logger.debug(f"Session object: {session.model_dump_json(indent=4)}")

    def _last_will() -> None:
        retrieval.utils.retrieval_status.RetrievalStatusList.update_item(
            session.retrieval_algorithm,
            session.atmospheric_profile_model,
            session.ctx.sensor_id,
            session.ctx.from_datetime,
            process_end_time=datetime.datetime.utcnow(),
        )
        logger.archive()

    def _graceful_teardown(*args: Any) -> None:
        logger.info(f"Container was killed")
        _last_will()
        exit(0)

    signal.signal(signal.SIGINT, _graceful_teardown)
    signal.signal(signal.SIGTERM, _graceful_teardown)
    logger.info("Established graceful teardown hook")

    try:
        logger.debug("Moving atmospheric profiles")
        move_profiles.run(config, session)

        logger.debug("Moving atmospheric datalogger files")
        move_log_files.run(config, logger, session)

        logger.debug("Moving interferograms")
        move_ifg_files.run(config, logger, session)
    except Exception as e:
        logger.warning(f"Inputs incomplete: {e}")
        _last_will()
        return

    logger.info(f"Running proffast")
    try:
        run_retrieval.run(session, test_mode=test_mode)
        logger.debug("Pylot execution was successful")
    except Exception as e:
        logger.exception(e, label="Proffast execution failed")

    # uncomment the following return if you want to observe the final
    # proffast outputs of one day in this working directory
    # return

    logger.info(f"Moving the outputs")
    try:
        move_outputs.run(config, logger, session, test_mode=test_mode)
        logger.info(f"Finished")
    except Exception as e:
        logger.exception(e, label="Moving outputs failed")

    _last_will()
