from rich.console import Console
from src.procedures import (
    download_map_data,
    initialize_environment,
    load_config,
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
    site = "ma"
    date = "210320"
    # TODO: Days to be processed marked by: 1. ifg folder on /mnt/meas... OR 2. No results folder on DSS yet OR 3. No ifg folder on DSS
    assert (
        site in CONFIG["sensor_coordinates"].keys()
    ), f"No coordinates given for site {site}"
    assert (
        site in CONFIG["sensor_serial_numbers"].keys()
    ), f"No serial number given for site {site}"

    blue_printer(f"20{date} - Preparing all input files")
    download_map_data.run(site, date, CONFIG)
    move_datalogger_files.run(site, date, CONFIG)
    move_ifg_files.run(site, date)
    create_input_file.run(site, date, CONFIG)

    # Run the pylot
    blue_printer(f"20{date} - Running the proffast pylot")
    run_proffast_pylot.run(site, date)

    # Check output correctness and move results and ifgs to DSS
    # TODO
