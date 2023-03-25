import os
from src import custom_types, utils
import tum_esm_utils

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
    tum_esm_utils.shell.run_shell_command(
        command=" ".join(
            [
                VENV_PATH,
                os.path.join(PYLOT_ROOT_DIR, "run.py"),
                session.container_id,
                session.pylot_config_path,
            ]
        )
    )
