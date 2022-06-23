import os
from src import utils, procedures
from src.utils import (
    load_config,
    Logger,
    add_to_input_warnings_list,
    remove_from_input_warnings_list,
)


def run():
    Logger.line(variant="=")
    Logger.info(f"Starting the automation with PID {os.getpid()}")

    try:
        CONFIG = load_config(validate=True)
    except:
        Logger.error("Config file invalid")
        Logger.exception()
        return

    try:
        retrieval_queue = utils.RetrievalQueue(CONFIG)

        for session in retrieval_queue:
            sensor = session["sensor"]
            date = session["date"]

            Logger.flush_date_logs()

            Logger.info(f"Starting {sensor}/{date}")
            procedures.initialize_session_environment.run(CONFIG, session)

            try:
                label = "vertical profiles"
                procedures.move_vertical_profiles.run(CONFIG, session)
                label = "datalogger files"
                procedures.move_datalogger_files.run(CONFIG, session)
                label = "ifgs files"
                procedures.move_ifg_files.run(CONFIG, session)
            except AssertionError as e:
                message = f"Inputs incomplete ({label})" + (
                    f": {e}" if "vertical" not in label else ""
                )
                Logger.warning(message)
                add_to_input_warnings_list(sensor, date, message)
                continue

            # inputs complete no warning to consider anymore
            remove_from_input_warnings_list(sensor, date)

            Logger.info(f"Running the pylot")
            try:
                procedures.run_proffast_pylot.run(CONFIG, session)
                Logger.debug(f"Pylot completed without errors")
            except Exception as e:
                Logger.warning(f"Pylot error: {e}")
                Logger.exception()

            # uncomment the following return if you want to observe the final
            # proffast outputs of one day in this working directory
            # return

            Logger.info(f"Moving the outputs")
            try:
                procedures.move_outputs.run(CONFIG, session)
                Logger.info(f"Finished")
            except AssertionError as e:
                Logger.error(f"Moving outputs failed: {e}")

    except KeyboardInterrupt:
        Logger.info("Keyboard interrupt")
        return
    except Exception:
        Logger.exception()
        return

    Logger.info(f"Automation is finished")
