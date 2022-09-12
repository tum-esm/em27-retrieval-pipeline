import os
import sys

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))

sys.path.append(f"{PROJECT_DIR}/src/prfpylot")
from src.prfpylot.prfpylot.pylot import Pylot


def run(config: dict, session):
    yaml_path = f"{PROJECT_DIR}/inputs/{session['sensor']}-pylot-config.yml"
    Pylot(yaml_path, logginglevel="debug").run(n_processes=1)
