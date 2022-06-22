import os
import sys

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))


def run(config: dict, session):
    if config["proffastVersion"] == "2.0.1":
        sys.path.append(f"{PROJECT_DIR}/src/pylot_1_0")
        from src.pylot_1_0.prfpylot.pylot import Pylot

    if config["proffastVersion"] == "2.1.1":
        sys.path.append(f"{PROJECT_DIR}/src/pylot_1_1")
        from src.pylot_1_1.prfpylot.pylot import Pylot

    yaml_path = f"{PROJECT_DIR}/inputs/{session['sensor']}-pylot-config.yml"
    Pylot(yaml_path, logginglevel="debug").run(n_processes=1)
