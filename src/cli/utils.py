import click
import os

dir = os.path.dirname
ROOT_DIR = dir(dir(dir(os.path.abspath(__file__))))
INTERPRETER_PATH = os.path.join(ROOT_DIR, ".venv", "bin", "python")
RUN_SCRIPT_PATH = os.path.join(ROOT_DIR, "automated-proffast-pylot", "run_retrieval.py")


def print_green(text: str) -> None:
    click.echo(click.style(text, fg="green"))


def print_red(text: str) -> None:
    click.echo(click.style(text, fg="red"))
