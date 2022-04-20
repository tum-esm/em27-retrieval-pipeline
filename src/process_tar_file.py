import os
import subprocess
from src import utils

dir = os.path.dirname
PROJECT_DIR = dir(dir(os.path.abspath(__file__)))


def run(date: str = None, files: dict = None):
    utils.print_blue(date, files["type"], "Processing tar file")
    result = subprocess.run(
        ["tar", "-xvf", files["tar"]],
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    os.remove(files["tar"])

    if result.returncode != 0:
        utils.print_red(date, files["type"], result.stderr.decode())
        return False
    if not os.path.isfile(files["dst"]):
        utils.print_red(date, files["type"], "tar file is empty")
        return False

    # store generated file in internal cache
    filepath_cache = f"{PROJECT_DIR}/cache/{files['cache']}"
    if os.path.isfile(filepath_cache):
        os.remove(filepath_cache)
    os.rename(files["dst"], filepath_cache)
    return True
