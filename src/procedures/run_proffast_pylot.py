import os
import sys

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))

# Required by imports within the proffastpylot project
sys.path.append(f"{PROJECT_DIR}/src/pylot_1_0_custom")

from src.pylot_1_0_custom.prfpylot.pylot import Pylot


def run(session):
    yaml_path = f"{PROJECT_DIR}/inputs/{session['sensor']}-pylot-config.yml"
    Pylot(yaml_path, logginglevel="debug").run(n_processes=1)
