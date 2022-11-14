import click
from .. import utils


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
