import sys
from rich.console import Console
from src import utils, procedures

PROJECT_DIR, CONFIG = utils.load_setup(validate=True)

# TODO: Use logging instead of printing
console = Console()
blue_printer = lambda message: console.print(f"[bold blue]{message}")
yellow_printer = lambda message: console.print(f"[bold yellow]{message}")
red_printer = lambda message: console.print(f"[bold red]{message}")


def run():
    # Determine next day to run proffast for
    blue_printer("Determining the next timeseries to process")
    retrieval_queue = utils.RetrievalQueue(sensor_names=CONFIG["sensorsToConsider"])

    for session in retrieval_queue:
        sensor = session["sensor"]
        date = session["date"]

        blue_printer(f"Starting retrieval session {sensor}/{date}")
        procedures.initialize_session_environment.run(session)

        blue_printer("Preparing all input files")
        try:
            procedures.move_vertical_profiles.run(session)
            procedures.move_datalogger_files.run(session)
            procedures.move_ifg_files.run(session)
        except AssertionError as e:
            yellow_printer(f"Inputs incomplete, skipping this date: {e}")
            procedures.removed_unfinished_inputs.run(session)
            continue
        except KeyboardInterrupt:
            sys.exit()

        blue_printer("Running the proffast pylot")
        try:
            procedures.run_proffast_pylot.run(session)
        except Exception as e:
            red_printer(f"Pylot error: {e}")
        except KeyboardInterrupt:
            sys.exit()

        blue_printer(f"Moving outputs")
        try:
            procedures.move_outputs.run(session)
        except AssertionError as e:
            red_printer(f"Moving outputs failed: {e}")
        except KeyboardInterrupt:
            sys.exit()

        # TODO: Upload results to database

    blue_printer("Queue is empty, no more dates to process")
