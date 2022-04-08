from src.utils import (
    download_map_data,
    initialize_environment,
    move_datalogger_files,
    move_ifg_files,
    create_input_file,
    run_proffast_pylot,
)

serial_numbers = {
    "ma": "061",
    "mb": "086",
    "mc": "115",
    "md": "116",
    "me": "117",
}


def run():

    # Test whether everything is set up correctly
    initialize_environment.run()

    # Determine next day to run proffast for
    site = "ma"
    date = "220322"
    # TODO

    # Download map files
    download_map_data.run(site, date)

    # Move datalogger files
    move_datalogger_files.run(site, serial_numbers[site], date)

    # Move ifg files
    move_ifg_files.run(site, date)

    # Create input yaml file
    create_input_file.run(site, serial_numbers[site], date)

    # Run proffast pylot
    run_proffast_pylot.run(site, date)

    # Check output correctness and move results to DSS
    # TODO
