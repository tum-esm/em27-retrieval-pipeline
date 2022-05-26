import sys
from rich.console import Console
from src.procedures import (
    initialize_session_environment,
    download_map_data,
    move_datalogger_files,
    move_ifg_files,
    removed_unfinished_inputs,
    run_proffast_pylot,
    move_outputs,
)
from src.utils.load_config import load_config
from src.utils.retrieval_queue import RetrievalQueue

# TODO: Use logging instead of printing
console = Console()
blue_printer = lambda message: console.print(f"[bold blue]{message}")
yellow_printer = lambda message: console.print(f"[bold yellow]{message}")
red_printer = lambda message: console.print(f"[bold red]{message}")


def run():
    CONFIG = load_config()

    # Determine next day to run proffast for
    blue_printer("Determining the next timeseries to process")
    retrieval_queue = RetrievalQueue(sensor_names=CONFIG["sensors_to_consider"])

    for session in retrieval_queue:
        sensor = session["sensor"]
        date = session["date"]
        if sensor != "ma" or date != 20220404:
            continue

        blue_printer(f"Starting retrieval session {sensor}/{date}")
        initialize_session_environment.run(session)

        blue_printer("Preparing all input files")
        try:
            download_map_data.run(session)
            move_datalogger_files.run(session)
            move_ifg_files.run(sensor)
        except AssertionError as e:
            yellow_printer(f"Inputs incomplete, skipping this date: {e}")
            removed_unfinished_inputs.run(session)
        except KeyboardInterrupt:
            sys.exit()

        blue_printer("Running the proffast pylot")
        try:
            run_proffast_pylot.run(session)
        except Exception as e:
            red_printer(f"Pylot error: {e}")
        except KeyboardInterrupt:
            sys.exit()

        blue_printer(f"Moving outputs")
        try:
            move_outputs.run(session)
        except AssertionError as e:
            red_printer(f"Moving outputs failed: {e}")
        except KeyboardInterrupt:
            sys.exit()

        # TODO: Upload results to database

    # TODO: if queue is empty, add 40 archived timeseries (only once)

    blue_printer("Queue is empty, no more dates to process")
