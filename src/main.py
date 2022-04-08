
from src.utils import move_ifg_files, run_proffast_pylot

serial_numbers = {
    "ma": "061",
    "mb": "086",
    "mc": "115",
    "md": "116",
    "me": "117",
}

def run():

    # 1. Determine next day to run proffast for
    site = "ma"
    date = "220322"

    # 2. Download map files

    # 3. Move datalogger files

    # 4. Move ifg files
    move_ifg_files.run(site, date)

    # 5. Create input yaml file

    # 6. Run proffast pylot
    run_proffast_pylot.run(site, date)
