import os
import shutil
from src import utils

PROJECT_DIR, CONFIG = utils.load_setup(validate=True)
DST = f"{PROJECT_DIR}/location-data"

if os.path.exists(DST):
    shutil.rmtree(DST)
os.system(f'git clone {CONFIG["locationRepository"]} {DST}')

os.system(f"pytest {DST}/tests/tests")
