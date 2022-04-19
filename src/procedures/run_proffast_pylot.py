import os
import sys

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))

# Required by imports within the proffastpylot project
sys.path.insert(0, f"{PROJECT_DIR}/proffastpylot")

from proffastpylot.prfpylot.pylot import Pylot


def run(sensor: str):
    print()
    Pylot(f"{PROJECT_DIR}/inputs/{sensor}-pylot-config.yml", logginglevel="info").run(
        n_processes=4
    )
    print()
