from src import utils, procedures
from src.utils import load_setup, Logger

PROJECT_DIR, CONFIG = load_setup(validate=True)


def run():
    Logger.info("-----------------------")
    Logger.info("Starting the automation")

    try:
        retrieval_queue = utils.RetrievalQueue(sensor_names=CONFIG["sensorsToConsider"])

        for session in retrieval_queue:
            sensor = session["sensor"]
            date = session["date"]

            message = lambda t: f"{sensor}/{date} - {t}"
            info = lambda t: Logger.info(message(t))
            warning = lambda t: Logger.info(message(t))
            error = lambda t: Logger.info(message(t))

            info(f"Starting")
            procedures.initialize_session_environment.run(session)

            inputs = {
                "vertical profiles": procedures.move_vertical_profiles,
                "datalogger": procedures.move_datalogger_files,
                "ifgs": procedures.move_ifg_files,
            }
            try:
                for label, input_module in inputs.items():
                    input_module.run(session)
            except AssertionError as e:
                if label == "vertical profiles":
                    info("Inputs incomplete (vertical profiles)")
                else:
                    warning(f"Inputs incomplete ({label}): {e}")
                continue

            info(f"Running the pylot")
            try:
                procedures.run_proffast_pylot.run(session)
            except Exception as e:
                warning(f"Pylot error: {e}")

            # uncomment the following return if you want to observe the final
            # proffast outputs of one day in this working directory
            # return

            info(f"Moving the outputs")
            try:
                procedures.move_outputs.run(session)
                info(f"Finished")
            except AssertionError as e:
                error(f"Moving outputs failed: {e}")
    except KeyboardInterrupt:
        Logger.info("Keyboard interrupt")
        return
    except Exception:
        Logger.exception()
        return

    Logger.info("Automation is finished")
