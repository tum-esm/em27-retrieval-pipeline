import click
from .. import utils


@click.command(help="Checks whether the em27-pipeline background process is running")
def pipeline_is_running() -> None:
    existing_pid = utils.process_is_running()
    if existing_pid is not None:
        utils.print_green(f"em27-pipeline is running with PID {existing_pid}")
    else:
        utils.print_red("em27-pipeline is not running")
