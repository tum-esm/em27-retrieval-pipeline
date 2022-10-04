import time
import click
import os
from .. import utils

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
INTERPRETER_PATH = os.path.join(PROJECT_DIR, ".venv", "bin", "python")
RUN_SCRIPT_PATH = os.path.join(PROJECT_DIR, "run-retrieval.py")


@click.command(
    help="Start the em27-pipeline as a background process. "
    + "Prevents spawning multiple processes"
)
def start_pipeline() -> None:
    current_pid = utils.process_is_running()
    if current_pid is not None:
        utils.print_red(f"Background process already exists with PID {current_pid}")
    else:
        os.system(f"nohup {INTERPRETER_PATH} {RUN_SCRIPT_PATH} &")
        time.sleep(0.5)
        new_pid = utils.process_is_running()
        if new_pid is None:
            utils.print_red(f"Could not start background process")
        else:
            utils.print_green(f"Started background process with PID {new_pid}")
