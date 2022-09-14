import os
from src import utils, procedures


def run() -> None:
    utils.Logger.line(variant="=")
    utils.Logger.info(f"Starting the automation with PID {os.getpid()}")

    try:
        config = utils.load_config(validate=True)
    except:
        utils.Logger.error("Config file invalid")
        utils.Logger.exception()
        return

    try:
        retrieval_queue = utils.RetrievalQueue(config)

        for session in retrieval_queue:
            sensor = session["sensor"]
            date = session["date"]

            utils.Logger.flush_session_logs()

            utils.Logger.info(f"Starting {sensor}/{date}")
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
                utils.Logger.warning(message)
                utils.InputWarningsList.add(sensor, date, message)
                continue

            # inputs complete no warning to consider anymore
            utils.InputWarningsList.remove(sensor, date)

            utils.Logger.info(f"Running the pylot")
            try:
                procedures.run_proffast_pylot.run(session)
                utils.Logger.debug(f"Pylot completed without errors")
            except Exception as e:
                utils.Logger.warning(f"Pylot error: {e}")
                utils.Logger.exception()

            # uncomment the following return if you want to observe the final
            # proffast outputs of one day in this working directory
            # return

            utils.Logger.info(f"Moving the outputs")
            try:
                procedures.move_outputs.run(config, session)
                utils.Logger.info(f"Finished")
            except AssertionError as e:
                utils.Logger.error(f"Moving outputs failed: {e}")

    except KeyboardInterrupt:
        utils.Logger.info("Keyboard interrupt")
        return
    except Exception:
        utils.Logger.exception()
        return

    utils.Logger.info(f"Automation is finished")
