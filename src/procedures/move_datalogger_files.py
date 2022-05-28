import os
import shutil
from rich.console import Console
from src import utils

PROJECT_DIR, CONFIG = utils.load_setup()

SRC = CONFIG["src"]["datalogger"]
DST = f"{PROJECT_DIR}/inputs"

console = Console()
yellow_printer = lambda message: console.print(f"[bold yellow]{message}")


def run(session):
    date = str(session["date"])

    src_dir = f'{SRC}/{session["sensor"]}_{str(session["serial_number"])[-2:]}'
    dst_dir = f'{DST}/{session["sensor"]}_pressure'
    assert os.path.isdir(src_dir)

    matching_files = list(
        filter(
            lambda f: f.startswith(f"{date[:4]}-{date[4:6]}-{date[6:]}_")
            and f.endswith(".dat"),
            os.listdir(src_dir),
        )
    )

    assert len(matching_files) > 0, "No datalogger file found"
    assert len(matching_files) < 2, f"Multiple datalogger files found: {matching_files}"

    src_file = f"{src_dir}/{matching_files[0]}"
    dst_file = f"{dst_dir}/{matching_files[0]}"
    with open(src_file, "r") as f:
        line_count = len(f.readlines())

    # 1440 minutes per day + 1 header line
    if line_count < 1441:
        yellow_printer(f"WARNING: Datalogger file only has {line_count}/1441 lines")
    assert line_count >= 30, "datalogger file has less than 30 entries"

    # copy datalogger file
    shutil.copy(src_file, dst_file)
