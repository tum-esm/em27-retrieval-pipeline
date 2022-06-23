import os
import sys
from tests.write_example_config_file import write_pylot_config

dir = os.path.dirname
PROJECT_DIR = dir(dir(os.path.abspath(__file__)))


def test_pylot_1_1():
    sys.path.append(f"{PROJECT_DIR}/src/pylot_1_1")
    from src.pylot_1_1.prfpylot.pylot import Pylot

    pylot_config_file = write_pylot_config("pylot_1_1")
    Pylot(pylot_config_file, logginglevel="info").run(n_processes=1)
