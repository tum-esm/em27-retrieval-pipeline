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
    logger.info(f"Starting {session.sensor_id}/{session.date}")

    label = "vertical profiles"
    try:
        move_vertical_profiles.run(config, session)
        label = "datalogger files"
        move_datalogger_files.run(config, logger, session)
        label = "ifgs files"
        move_ifg_files.run(config, logger, session)
    except AssertionError as e:
        message = f"Inputs incomplete ({label})" + (
            f": {e}" if "vertical" not in label else ""
        )
        logger.warning(message)
        interfaces.InputWarningsInterface.add(session.sensor_id, session.date, message)
        return

    # inputs complete no warning to consider anymore
    interfaces.InputWarningsInterface.remove(session.sensor_id, session.date)

    logger.info(f"Running the pylot")
    try:
        run_proffast_pylot.run(session, logger)
        logger.debug(f"Pylot completed without errors")
    except Exception as e:
        logger.warning(f"Pylot error: {e}")
        logger.exception()

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
