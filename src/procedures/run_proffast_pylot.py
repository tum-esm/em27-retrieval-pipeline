import sys
from src.utils import load_setup

PROJECT_DIR, CONFIG = load_setup()

# Required by imports within the proffastpylot project
sys.path.append(f"{PROJECT_DIR}/src/pylot")

from src.pylot.prfpylot.pylot import Pylot


def run(session):
    yaml_path = f"{PROJECT_DIR}/inputs/{session['sensor']}-pylot-config.yml"
    Pylot(yaml_path, logginglevel="info").run(n_processes=1)
