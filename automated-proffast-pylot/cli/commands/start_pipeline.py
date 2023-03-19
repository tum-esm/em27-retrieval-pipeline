import click
from ..utils import INTERPRETER_PATH, RUN_SCRIPT_PATH, print_green
import tum_esm_utils


@click.command(
    help="Start the em27-pipeline as a background process. "
    + "Prevents spawning multiple processes"
)
def start_pipeline() -> None:
    new_pid = tum_esm_utils.processes.start_background_process(
        INTERPRETER_PATH, RUN_SCRIPT_PATH
    )
    print_green(f"Started background process with PID {new_pid}")
