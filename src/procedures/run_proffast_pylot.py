import sys
from src import utils

PROJECT_DIR, CONFIG = utils.load_setup()

# Required by imports within the proffastpylot project
sys.path.append(f"{PROJECT_DIR}/src/pylot")

from src.pylot.prfpylot.pylot import Pylot


def run(session):
    sensor = session["sensor"]
    Pylot(f"{PROJECT_DIR}/inputs/{sensor}-pylot-config.yml", logginglevel="info").run(
        n_processes=1
    )
