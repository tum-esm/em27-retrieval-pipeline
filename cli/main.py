import click
import os
import sys

dir = os.path.dirname
PROJECT_DIR = dir(dir(os.path.abspath(__file__)))
sys.path.append(PROJECT_DIR)


@click.group()
def cli() -> None:
    pass


if __name__ == "__main__":
    cli.main(prog_name="em27-pipeline-cli")
