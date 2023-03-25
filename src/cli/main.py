import click
import os
import sys

dir = os.path.dirname
PROJECT_DIR = dir(dir(os.path.abspath(__file__)))
sys.path.append(PROJECT_DIR)

from cli.commands import (
    start_pipeline,
    stop_pipeline,
    pipeline_is_running,
)


@click.group()
def cli() -> None:
    pass


cli.add_command(start_pipeline, name="start")
cli.add_command(stop_pipeline, name="stop")
cli.add_command(pipeline_is_running, name="is-running")


if __name__ == "__main__":
    cli.main(prog_name="em27-pipeline-cli")
