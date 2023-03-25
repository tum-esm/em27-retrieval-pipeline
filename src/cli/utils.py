import click


def print_green(text: str) -> None:
    click.echo(click.style(text, fg="green"))


def print_red(text: str) -> None:
    click.echo(click.style(text, fg="red"))
