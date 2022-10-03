import subprocess
import click
import os
from .. import utils

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
INTERPRETER_PATH = os.path.join(PROJECT_DIR, ".venv", "bin", "python")
CORE_SCRIPT_PATH = os.path.join(PROJECT_DIR, "run-retrieval.py")


@click.command(
    help="Start the em27-pipeline as a background process. "
    + "Prevents spawning multiple processes"
)
def start_pipeline() -> None:
    existing_pid = utils.process_is_running()
    if existing_pid is not None:
        utils.print_red(f"Background process already exists with PID {existing_pid}")
    else:
        p = subprocess.Popen(
            [INTERPRETER_PATH, CORE_SCRIPT_PATH],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        utils.print_green(f"Started background process with PID {p.pid}")
