from typing import Any
from src import utils, retrieval
import signal
from . import (
    move_log_files,
    move_profiles,
    move_ifg_files,
    move_outputs,
    run_retrieval,
)


def run(
    config: utils.config.Config,
    session: utils.types.RetrievalSession,
) -> None:
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    logger = retrieval.utils.logger.Logger(
        container_id=session.ctn.container_id
    )
    logger.info(f"Starting session in container id {session.ctn.container_id}")
    logger.info(
        f"Sensor {session.ctx.sensor_id}: " +
        f"from {session.ctx.from_datetime} to {session.ctx.to_datetime}"
    )
    logger.debug(f"Session object: {session.model_dump_json(indent=4)}")

    def _graceful_teardown(*args: Any) -> None:
        logger.info(f"Container was killed")
        logger.archive()
        exit(0)

    signal.signal(signal.SIGINT, _graceful_teardown)
    signal.signal(signal.SIGTERM, _graceful_teardown)
    logger.info("Established graceful teardown hook")

    def log_input_warning(message: str) -> None:
        retrieval.dispatching.input_warning_list.InputWarningsInterface.add(
            session.ctx.sensor_id, session.ctx.from_datetime, message
        )
        logger.warning(message)
        logger.archive()

    try:
        move_profiles.run(config, session)
    except Exception as e:
        log_input_warning(f"Inputs incomplete (atmospheric profiles): {e}")
        return

    try:
        move_log_files.run(config, logger, session)
    except Exception as e:
        log_input_warning(f"Inputs incomplete (datalogger files): {e}")
        return

    try:
        move_ifg_files.run(config, logger, session)
    except Exception as e:
        log_input_warning(f"Inputs incomplete (ifg files): {e}")
        return

    # inputs complete no warning to consider anymore
    retrieval.dispatching.input_warning_list.InputWarningsInterface.remove(
        session.ctx.sensor_id,
        session.ctx.from_datetime,
    )

    logger.info(f"Running proffast")
    try:
        run_retrieval.run(session)
        logger.debug("Pylot execution was successful")
    except Exception as e:
        logger.exception(e, label="Proffast execution failed")

    # uncomment the following return if you want to observe the final
    # proffast outputs of one day in this working directory
    # return

    logger.info(f"Moving the outputs")
    try:
        move_outputs.run(config, logger, session)
        logger.info(f"Finished")
    except Exception as e:
        logger.exception(e, label="Moving outputs failed")

    logger.archive()
