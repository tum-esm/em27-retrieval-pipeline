import os
import shutil
from rich.console import Console

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))

SRC = "/home/esm/datalogger2zeno"
DST = f"{PROJECT_DIR}/inputs"

console = Console()
yellow_printer = lambda message: console.print(f"[bold yellow]{message}")


def run(site: str, date: str, config: dict):
    src_dir = f'{SRC}/{site}_{str(config["sensor_serial_numbers"][site])[-2:]}'
    dst_dir = f"{DST}/{site}/pressure"
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
            # TODO: Use logging instead of printing
            yellow_printer(f"WARNING: Datalogger file only has {line_count}/1441 lines")

    # copy datalogger file
    shutil.copy(src_file, dst_file)
