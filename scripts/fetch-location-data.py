import os
import shutil
import sys

dir = os.path.dirname
PROJECT_DIR = dir(dir(os.path.abspath(__file__)))
sys.path.append(PROJECT_DIR)

from src import utils

CONFIG = utils.load_config(validate=True)
DST = f"{PROJECT_DIR}/location-data"

if os.path.exists(DST):
    shutil.rmtree(DST)
os.system(f'git clone {CONFIG["locationRepository"]} {DST}')

os.system(f"pytest {DST}/tests/tests")
