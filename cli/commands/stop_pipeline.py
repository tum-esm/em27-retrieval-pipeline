import click
import os
from .. import utils

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
INTERPRETER_PATH = os.path.join(PROJECT_DIR, ".venv", "bin", "python")
CORE_SCRIPT_PATH = os.path.join(PROJECT_DIR, "run-pyra-core.py")


@click.command(help="Stop the em27-pipeline background process")
def stop_pipeline() -> None:
    termination_pids = utils.terminate_processes()
    if len(termination_pids) == 0:
        utils.print_red("No active process to be terminated")
    else:
        utils.print_green(
            f"Terminated {len(termination_pids)} em27-pipeline background "
            + f"processe(s) with PID(s) {termination_pids}"
        )
