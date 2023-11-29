import datetime
from typing import Any
import signal
from src import utils, retrieval
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
        retrieval.utils.process_status.ProcessStatusList.update_item(
            session.ctx.sensor_id,
            session.ctx.from_datetime,
            process_end_time=datetime.datetime.utcnow(),
        )
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

    label: str = "atmospheric profiles"
    try:
        move_profiles.run(config, session)
        label = "datalogger files"
        move_log_files.run(config, logger, session)
        label = "ifg files"
        move_ifg_files.run(config, logger, session)
        pass
    except Exception as e:
        log_input_warning(f"Inputs incomplete ({label}): {e}")
        retrieval.utils.process_status.ProcessStatusList.update_item(
            session.ctx.sensor_id,
            session.ctx.from_datetime,
            process_end_time=datetime.datetime.utcnow(),
        )
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
    retrieval.utils.process_status.ProcessStatusList.update_item(
        session.ctx.sensor_id,
        session.ctx.from_datetime,
        process_end_time=datetime.datetime.utcnow(),
    )
