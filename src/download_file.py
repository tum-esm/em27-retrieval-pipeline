import os
import subprocess
import time
from src import utils, load_config

dir = os.path.dirname
PROJECT_DIR = dir(dir(os.path.abspath(__file__)))
CONFIG = load_config.run()


# TODO: Rewrite with tenacity

def run(start_date: str, end_date: str):
    running_time = 0
    for filetype in ["map", "mod"]:
        tar_filename = utils.get_tar_filename(filetype, start_date, end_date)
        while running_time < CONFIG["downloadTimeoutSeconds"]:
            subprocess.run(
                [
                    "wget",
                    "--user",
                    "anonymous",
                    "--password",
                    CONFIG["user"],
                    f"ftp://ccycle.gps.caltech.edu/upload/modfiles/tar/{filetype}s/{tar_filename}",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            if os.path.isfile(tar_filename):
                break

            running_time += 8
            time.sleep(8)
