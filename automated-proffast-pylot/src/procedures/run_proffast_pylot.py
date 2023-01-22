import os
import subprocess
from src import custom_types, utils

dirname = os.path.dirname
PROJECT_DIR = dirname(dirname(dirname(os.path.abspath(__file__))))
VENV_PATH = os.path.join(
    dirname(dirname(dirname(dirname(os.path.abspath(__file__))))),
    ".venv",
    "bin",
    "python",
)
PYLOT_ROOT_DIR = os.path.join(PROJECT_DIR, "src", "prfpylot")


def run(session: custom_types.Session, logger: utils.Logger) -> None:
    result = subprocess.run(
        [
            VENV_PATH,
            os.path.join(PYLOT_ROOT_DIR, "run.py"),
            session.pylot_container.container_id,
            session.pylot_container.pylot_config_path,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    logger.info(f"Pylot instance result {result.returncode}")
    logger.info(f"Pylot Execution Logs: {result.stdout}")
    logger.error(f"Pylot Execution Logs: {result.stderr}")
