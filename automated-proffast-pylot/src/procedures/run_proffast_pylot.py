import os
import sys
from src import types
from src.types.pylot_factory import PylotFactory
dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))

sys.path.append(f"{PROJECT_DIR}/src/prfpylot")
#from src.prfpylot.prfpylot.pylot import Pylot


def run(session: types.SessionDict, pylot_factory: PylotFactory) -> None:
    yaml_path = f"{PROJECT_DIR}/inputs/{session['container_id']}/{session['sensor']}-pylot-config.yml"
    result = pylot_factory.execute_pylot(session["container_id"], yaml_path, 1)
    print(f"Pylot instance result {result.returncode}")
    print(f"{result.stderr}")
    print(f"{result.stdout}")
