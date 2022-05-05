import os
import subprocess
import time
from src import utils, load_config

dir = os.path.dirname
PROJECT_DIR = dir(dir(os.path.abspath(__file__)))
CONFIG = load_config.run()


def run(start_date: str, end_date: str):
    running_time = 0
    for filetype in ["map", "mod"]:
        possible_tar_filenames = utils.get_possible_tar_filenames(filetype, start_date, end_date)
        
        while running_time < CONFIG["downloadTimeoutSeconds"]:
            for filename in possible_tar_filenames:
                subprocess.run(
                    [
                        "wget",
                        "--user",
                        "anonymous",
                        "--password",
                        CONFIG["user"],
                        f"ftp://ccycle.gps.caltech.edu/upload/modfiles/tar/{filetype}s/{filename}",
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                
            if any(map(os.path.isfile, possible_tar_filenames)):
                break

            running_time += 8
            time.sleep(8)
