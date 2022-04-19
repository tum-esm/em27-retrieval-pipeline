import sys
from rich.console import Console
from src.procedures import (
    load_config,
    initialize_environment,
    determine_next_dates,
    download_map_data,
    move_datalogger_files,
    move_ifg_files,
    create_input_file,
    run_proffast_pylot,
)

console = Console()

blue_printer = lambda message: console.print(f"[bold blue]{message}")


def run():
    # Load config, test setup, clear data directories
    blue_printer("Initializing the environment")
    CONFIG = load_config.run()
    initialize_environment.run(CONFIG)

    # Determine next day to run proffast for
    blue_printer("Determining the next timeseries to process")
    next_day = determine_next_dates.run(CONFIG)
    print_label = f"{next_day['site']}/{'-'.join(next_day['dates'])}"
    if len(next_day["dates"]) == 0:
        sys.exit()

    # TODO: Handle dates that could not be processed

    blue_printer(f"{print_label} - Preparing all input files")
    for date in next_day["dates"]:
        download_map_data.run(next_day["site"], date, CONFIG)
        move_datalogger_files.run(next_day["site"], date, CONFIG)
        move_ifg_files.run(next_day["site"], date)

    blue_printer(f"{print_label} - Creating input YAML file")
    create_input_file.run(next_day["site"], CONFIG)

    blue_printer(f"{print_label} - Running the proffast pylot")
    run_proffast_pylot.run(next_day["site"], date)

    # Check output correctness and move results and ifgs to DSS
    # TODO
