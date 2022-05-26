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
from src.utils.retrieval_session_queue import RetrievalSessionQueue

console = Console()
blue_printer = lambda message: console.print(f"[bold blue]{message}")
yellow_printer = lambda message: console.print(f"[bold yellow]{message}")
red_printer = lambda message: console.print(f"[bold red]{message}")
MAX_PARALLEL_PROCESSES = 1


def run():
    CONFIG = load_config()

    # Determine next day to run proffast for
    blue_printer("Determining the next timeseries to process")
    session_queue = RetrievalSessionQueue(sensor_names=CONFIG["sensors_to_consider"])

    # one session sensor-location-combination
    for session in session_queue:

        date_processing_index = 0
        sensor = session["sensor"]

        blue_printer("Resetting Environment")
        initialize_session_environment.run(session)

        while date_processing_index < len(session["dates"]):
            dates_to_be_pyloted = []

            # take the next N dates where inputs are valid (N = MAX_PARALLEL_PROCESSES)
            while True:
                date = session["dates"][date_processing_index]

                blue_printer(f"{sensor}/{date} - Preparing all input files")
                try:
                    download_map_data.run(sensor, date, CONFIG)
                    move_datalogger_files.run(sensor, date, CONFIG)
                    move_ifg_files.run(sensor, date)
                    dates_to_be_pyloted.append(date)
                except AssertionError:
                    yellow_printer(
                        f"{sensor}/{date} - Inputs incomplete, skipping this date"
                    )
                    removed_unfinished_inputs.run(sensor, date)

                date_processing_index += 1

                if (len(dates_to_be_pyloted) == MAX_PARALLEL_PROCESSES) or (
                    date_processing_index == len(session["dates"])
                ):
                    break

            blue_printer(
                f"{sensor}/{','.join(dates_to_be_pyloted)} - Running the proffast pylot"
            )
            try:
                run_proffast_pylot.run(
                    sensor, parallel_processes=MAX_PARALLEL_PROCESSES
                )
            except Exception as e:
                red_printer(
                    f"{sensor}/{','.join(dates_to_be_pyloted)} - Runtime error in pylot: {e}"
                )

            blue_printer(f"{sensor}/{','.join(dates_to_be_pyloted)} - Moving outputs")
            move_output_message = move_outputs.run(sensor, dates_to_be_pyloted, CONFIG)
            if move_output_message == "failed":
                red_printer(
                    f"{sensor}/{','.join(dates_to_be_pyloted)} - Moving outputs failed"
                )
            else:
                blue_printer(
                    f"{sensor}/{','.join(dates_to_be_pyloted)} - Moving outputs: {move_output_message}"
                )

    # TODO: if queue is empty, add 50 archived timeseries (only once)

    blue_printer("Queue is empty, no more dates to process")
