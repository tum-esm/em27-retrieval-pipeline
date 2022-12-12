import os
from src import utils, procedures
from src.types.pylot_factory import PylotFactory
import multiprocessing


def run() -> None:
    main_logger = utils.Logger('main')
    pool = multiprocessing.Pool()
    pylot_factory = PylotFactory(main_logger)

    main_logger.line(variant="=")
    main_logger.info(f"Starting the automation with PID {os.getpid()}")

    try:
        config = utils.load_config(validate=True)
    except:
        main_logger.error("Config file invalid")
        main_logger.exception()
        return


    try:
        retrieval_queue = utils.RetrievalQueue(config, pylot_factory)

        for session in retrieval_queue:
            sensor = session["sensor"]
            date = session["date"]
            container_id = session["container_id"]
            container_path = session["container_path"]

            main_logger.info(m=f"Running session: {sensor}, {date} in container {container_id} at path {container_path}")

            logger = utils.Logger(container_id)
            logger.flush_session_logs()
            logger.info(f"Starting {sensor}/{date}")

            # Get container path
            procedures.initialize_session_environment.run(session)

            label = "vertical profiles"
            try:
                procedures.move_vertical_profiles.run(config, session)
                label = "datalogger files"
                procedures.move_datalogger_files.run(config, session)
                label = "ifgs files"
                procedures.move_ifg_files.run(config, session)
            except AssertionError as e:
                message = f"Inputs incomplete ({label})" + (
                    f": {e}" if "vertical" not in label else ""
                )
                logger.warning(message)
                utils.InputWarningsList.add(sensor, date, message)
                continue

            # inputs complete no warning to consider anymore
            utils.InputWarningsList.remove(sensor, date)

            logger.info(f"Running the pylot")
            try:
                procedures.run_proffast_pylot.run(session)
                logger.debug(f"Pylot completed without errors")
            except Exception as e:
                logger.warning(f"Pylot error: {e}")
                logger.exception()

            # uncomment the following return if you want to observe the final
            # proffast outputs of one day in this working directory
            # return

            logger.info(f"Moving the outputs")
            try:
                procedures.move_outputs.run(config, session)
                logger.info(f"Finished")
            except AssertionError as e:
                logger.error(f"Moving outputs failed: {e}")

    except KeyboardInterrupt:
        main_logger.info("Keyboard interrupt")
        return
    except Exception:
        main_logger.exception()
        return

    main_logger.info(f"Automation is finished")
