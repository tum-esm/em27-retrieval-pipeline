import os
import sys
import click
import tum_esm_utils

_PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(
    __file__, current_depth=2
)
_RUN_SCRIPT_PATH = os.path.join(_PROJECT_DIR, "src", "run_retrieval.py")

sys.path.append(_PROJECT_DIR)
from src import utils, retrieval


def print_green(text: str) -> None:
    click.echo(click.style(text, fg="green"))


def print_red(text: str) -> None:
    click.echo(click.style(text, fg="red"))


@click.command(
    help="Start the automated retrieval as a background " +
    "process. Prevents spawning multiple processes"
)
def _start() -> None:
    new_pid = tum_esm_utils.processes.start_background_process(
        sys.executable, _RUN_SCRIPT_PATH
    )
    print_green(
        f"Started automated retrieval background process with PID {new_pid}"
    )


@click.command(
    help="Checks whether the automated retrieval background process is running"
)
def _is_running() -> None:
    existing_pids = tum_esm_utils.processes.get_process_pids(_RUN_SCRIPT_PATH)
    if len(existing_pids) > 0:
        print_green(
            f"automated retrieval is running with PID(s) {existing_pids}"
        )
    else:
        print_red("automated retrieval is not running")


@click.command(help="Stop the automated retrieval background process")
def _stop() -> None:
    termination_pids = tum_esm_utils.processes.terminate_process(
        _RUN_SCRIPT_PATH
    )
    if len(termination_pids) == 0:
        print_red("No active process to be terminated")
    else:
        print_green(
            f"Terminated {len(termination_pids)} automated retrieval " +
            f"background processe(s) with PID(s) {termination_pids}"
        )


# TODO: remove this once automatic printing is implemented
@click.command(help="Print out the retrieval queue")
def _print_queue() -> None:
    main_logger = retrieval.utils.logger.Logger("main", print_only=True)
    config = utils.config.Config.load()
    retrieval_queue = retrieval.dispatching.retrieval_queue.RetrievalQueue(
        config, main_logger, verbose_reasoning=True
    )

    while True:
        next_sensor_data_context = retrieval_queue.get_next_item()
        if next_sensor_data_context is None:
            main_logger.info("✨ done")
            break
        main_logger.info(
            f"{next_sensor_data_context.sensor_id}/" +
            f"{next_sensor_data_context.from_datetime}-" +
            f"{next_sensor_data_context.to_datetime}"
        )


@click.group()
def retrieval_command_group() -> None:
    pass


retrieval_command_group.add_command(_start, name="start")
retrieval_command_group.add_command(_stop, name="stop")
retrieval_command_group.add_command(_is_running, name="is-running")
retrieval_command_group.add_command(_print_queue, name="print-queue")


@click.group()
def cli() -> None:
    pass


cli.add_command(retrieval_command_group, name="retrieval")

if __name__ == "__main__":
    cli.main(prog_name="em27-pipeline-cli")
