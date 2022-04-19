import sys
from rich.console import Console
from src.procedures import (
    load_config,
    initialize_environment,
    determine_unprocessed_dates,
    download_map_data,
    move_datalogger_files,
    move_ifg_files,
    removed_unfinished_inputs,
    run_proffast_pylot,
)

console = Console()

blue_printer = lambda message: console.print(f"[bold blue]{message}")
yellow_printer = lambda message: console.print(f"[bold yellow]{message}")

MAX_PARALLEL_PROCESSES = 4


def dates_queue_is_empty(q):
    return all([len(x["dates"]) == 0 for x in q])


def remove_date_from_queue(q, sensor, date):
    assert q[0]["sensor"] == sensor
    q[0]["dates"] = [d for d in q[0]["dates"] if d != date]
    return q


def run():
    # Load config, test setup, clear data directories
    blue_printer("Initializing the environment")
    CONFIG = load_config.run()

    # Determine next day to run proffast for
    blue_printer("Determining the next timeseries to process")
    next_dates = determine_unprocessed_dates.run(CONFIG)

    while not dates_queue_is_empty(next_dates):
        blue_printer(f"Resetting Environment")
        initialize_environment.run(CONFIG)

        next_dates = list(sorted(next_dates, key=lambda x: -len(x["dates"])))
        sensor = next_dates[0]["sensor"]
        dates_to_be_pyloted = []

        for date in [*next_dates[0]["dates"]]:
            next_dates = remove_date_from_queue(next_dates, sensor, date)

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
                removed_unfinished_inputs.run(sensor)

            if len(dates_to_be_pyloted) == MAX_PARALLEL_PROCESSES:
                break

        blue_printer(
            f"{sensor}/{'-'.join(dates_to_be_pyloted)} - Running the proffast pylot"
        )
        run_proffast_pylot.run(sensor)

        sys.exit()

        # Check output correctness and move results and ifgs to DSS
        # TODO
