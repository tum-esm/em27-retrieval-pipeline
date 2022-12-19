import os
import sys
from src import types
from src.types.pylot_factory import PylotFactory
from src.utils.logger import Logger

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))

sys.path.append(f"{PROJECT_DIR}/src/prfpylot")
#from src.prfpylot.prfpylot.pylot import Pylot


def run(session: types.SessionDict, pylot_factory: PylotFactory, logger: Logger) -> None:
    yaml_path = f"{PROJECT_DIR}/inputs/{session['container_id']}/{session['sensor']}-pylot-config.yml"
    result = pylot_factory.execute_pylot(session["container_id"], yaml_path, 1)
    logger.info(f"Pylot instance result {result.returncode}")
    logger.info(f"Pylot Execution Logs: {result.stdout}")
    logger.error(f"Pylot Execution Logs: {result.stderr}")
