import os
import sys

dir = os.path.dirname
PROJECT_DIR = dir(dir(os.path.abspath(__file__)))

sys.path.append(f"{PROJECT_DIR}/src/pylot")
from prfpylot.pylot import Pylot


yaml_path = f"{PROJECT_DIR}/simulation/mc-pylot-config.yml"
Pylot(yaml_path, logginglevel="info").run(n_processes=1)
