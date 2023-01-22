from src import custom_types, utils, interfaces, procedures
import signal


def run(
    config: custom_types.Config,
    session: custom_types.Session,
    pylot_factory: interfaces.PylotFactory,
):
    # Handle sig int
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    sensor = session["sensor"]
    date = session["date"]
    container_id = session["container_id"]

    logger = utils.Logger(container_id)
    logger.flush_session_logs()
    logger.info(f"Starting {sensor}/{date}")

    # Get container path
    procedures.create_session.run(session)

    label = "vertical profiles"
    try:
        procedures.move_vertical_profiles.run(config, session)
        label = "datalogger files"
        procedures.move_datalogger_files.run(config, logger, session)
        label = "ifgs files"
        procedures.move_ifg_files.run(config, logger, session)
    except AssertionError as e:
        message = f"Inputs incomplete ({label})" + (
            f": {e}" if "vertical" not in label else ""
        )
        logger.warning(message)
        utils.InputWarningsList.add(sensor, date, message)
        return

    # inputs complete no warning to consider anymore
    utils.InputWarningsList.remove(sensor, date)

    logger.info(f"Running the pylot")
    try:
        procedures.run_proffast_pylot.run(session, pylot_factory, logger)
        logger.debug(f"Pylot completed without errors")
    except Exception as e:
        logger.warning(f"Pylot error: {e}")
        logger.exception()

    # uncomment the following return if you want to observe the final
    # proffast outputs of one day in this working directory
    # return

    logger.info(f"Moving the outputs")
    try:
        procedures.move_outputs.run(config, logger, session)
        logger.info(f"Finished")
    except AssertionError as e:
        logger.error(f"Moving outputs failed: {e}")
