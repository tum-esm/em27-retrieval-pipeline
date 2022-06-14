import os
from src import utils, procedures
from src.utils import load_config, Logger


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
            procedures.initialize_session_environment.run(session)

            inputs = {
                "vertical profiles": procedures.move_vertical_profiles,
                "datalogger": procedures.move_datalogger_files,
                "ifgs": procedures.move_ifg_files,
            }
            try:
                for label, input_module in inputs.items():
                    input_module.run(CONFIG, session)
            except AssertionError as e:
                if label == "vertical profiles":
                    Logger.info("Inputs incomplete (vertical profiles)")
                else:
                    Logger.warning(f"Inputs incomplete ({label}): {e}")
                continue

            Logger.info(f"Running the pylot")
            try:
                procedures.run_proffast_pylot.run(session)
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
