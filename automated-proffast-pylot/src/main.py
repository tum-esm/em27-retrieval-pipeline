from multiprocessing.pool import AsyncResult
import os
from typing import List
from src import utils, procedures
from src.custom_types.pylot_factory import PylotFactory
from src.custom_types.session import SessionDict
from src.custom_types.config import ConfigDict
import multiprocessing as mp
import signal


def __process_session(
    config: ConfigDict, session: SessionDict, pylot_factory: PylotFactory
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
    procedures.initialize_session_environment.run(session)

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


def run() -> None:
    main_logger = utils.Logger("main")
    pylot_factory = PylotFactory(main_logger)
    pool = mp.Pool(4)

    main_logger.line(variant="=")
    main_logger.info(f"Starting the automation with PID {os.getpid()}")

    try:
        config = utils.load_config(validate=True)
    except:
        main_logger.error("Config file invalid")
        main_logger.exception()
        return

    try:
        retrieval_queue = utils.RetrievalQueue(config, main_logger, pylot_factory)
        results: List[AsyncResult] = []
        for session in retrieval_queue:
            main_logger.info(
                m=f"Running session: {session['sensor']}, {session['date']} in container {session['container_id']} at path {session['container_path']}"
            )
            result: AsyncResult = pool.apply_async(
                func=__process_session, args=(config, session, pylot_factory)
            )
            results.append(result)
        [result.get() for result in results]
    except KeyboardInterrupt:
        main_logger.info("Keyboard interrupt")
        pylot_factory.clean_up()
        pool.terminate()
        return
    except Exception:
        main_logger.exception()
        pylot_factory.clean_up()
        pool.terminate()
        return

    pylot_factory.clean_up()
    main_logger.info(f"Automation is finished")
