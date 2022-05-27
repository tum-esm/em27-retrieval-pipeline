import os
import subprocess
import time
from src import download_profiles


def run(start_date: str, end_date: str, config: dict):
    running_time = 0
    for filetype in ["map", "mod"]:
        possible_tar_filenames = download_profiles.utils.get_possible_tar_filenames(filetype, start_date, end_date, config)
        
        while running_time < config["downloadTimeoutSeconds"]:
            for filename in possible_tar_filenames:
                subprocess.run(
                    [
                        "wget",
                        "--user",
                        "anonymous",
                        "--password",
                        config["user"],
                        f"ftp://ccycle.gps.caltech.edu/upload/modfiles/tar/{filetype}s/{filename}",
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=60,
                )
                
            if any(map(os.path.isfile, possible_tar_filenames)):
                break

            running_time += 8
            time.sleep(8)
