import os
import subprocess
import time
from src.utils import FileUtils, load_setup

PROJECT_DIR, CONFIG = load_setup(validate=False)


def run(query):
    running_time = 0
    for filetype in ["map", "mod"]:
        possible_tar_filenames = FileUtils.get_possible_tar_filenames(filetype, query)
        
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
                    timeout=60,
                )
                
            if any(map(os.path.isfile, possible_tar_filenames)):
                break

            running_time += 8
            time.sleep(8)
