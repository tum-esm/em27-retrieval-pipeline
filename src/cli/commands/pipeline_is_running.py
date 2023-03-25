import click
from ..utils import RUN_SCRIPT_PATH, print_green, print_red
import tum_esm_utils


@click.command(help="Checks whether the em27-pipeline background process is running")
def pipeline_is_running() -> None:
    existing_pids = tum_esm_utils.processes.get_process_pids(RUN_SCRIPT_PATH)
    if len(existing_pids) > 0:
        print_green(f"em27-pipeline is running with PID(s) {existing_pids}")
    else:
        print_red("em27-pipeline is not running")
