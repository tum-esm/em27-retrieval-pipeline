import click
import tum_esm_utils
from ..utils import RUN_SCRIPT_PATH, print_green, print_red


@click.command(help="Stop the em27-pipeline background process")
def stop_pipeline() -> None:
    termination_pids = tum_esm_utils.processes.terminate_process(RUN_SCRIPT_PATH)
    if len(termination_pids) == 0:
        print_red("No active process to be terminated")
    else:
        print_green(
            f"Terminated {len(termination_pids)} em27-pipeline background "
            + f"processe(s) with PID(s) {termination_pids}"
        )
