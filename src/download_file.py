import os
import subprocess
import time
from src import utils

dir = os.path.dirname
PROJECT_DIR = dir(dir(os.path.abspath(__file__)))


def run(date: str = None, config: dict = None, files: dict = None):
    utils.print_blue(date, files["type"], "Downloading file")

    running_time = 0
    while running_time < config["downloadTimeoutSeconds"]:
        subprocess.run(
            [
                "wget",
                "--user",
                "anonymous",
                "--password",
                config["user"],
                f"ftp://ccycle.gps.caltech.edu/upload/modfiles/tar/{files['type']}s/{files['tar']}",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if os.path.isfile(files["tar"]):
            return True

        running_time += 8
        time.sleep(8)

    utils.print_blue(date, files["type"], "Download timed out")
    return False
