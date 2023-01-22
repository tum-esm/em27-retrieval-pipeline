from src import custom_types, interfaces, utils
import signal

from . import (
    move_datalogger_files,
    move_vertical_profiles,
    move_ifg_files,
    run_proffast_pylot,
    move_outputs,
)


def run(config: custom_types.Config, session: custom_types.Session):
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    logger = utils.Logger(container_id=session.container_id)
    logger.info(f"Starting session {session.sensor_id}/{session.date}")

    def log_input_warning(message: str):
        interfaces.InputWarningsInterface.add(session.sensor_id, session.date, message)
        logger.warning(message)
        logger.archive()

    try:
        move_vertical_profiles.run(config, session)
    except AssertionError as e:
        log_input_warning(f"Inputs incomplete (vertical profiles)")
        return

    try:
        move_datalogger_files.run(config, logger, session)
    except AssertionError as e:
        log_input_warning(f"Inputs incomplete (datalogger files): {e}")
        return

    try:
        move_ifg_files.run(config, logger, session)
    except AssertionError as e:
        log_input_warning(f"Inputs incomplete (ifg files): {e}")
        return

    # inputs complete no warning to consider anymore
    interfaces.InputWarningsInterface.remove(session.sensor_id, session.date)

    logger.info(f"Running the pylot")
    try:
        run_proffast_pylot.run(session, logger)
        logger.debug("Pylot execution was successful")
    except Exception as e:
        logger.debug(f"Pylot execution failed: {e}")

    # uncomment the following return if you want to observe the final
    # proffast outputs of one day in this working directory
    # return

    logger.info(f"Moving the outputs")
    try:
        move_outputs.run(config, logger, session)
        logger.info(f"Finished")
    except AssertionError as e:
        logger.error(f"Moving outputs failed: {e}")

    logger.archive()
