import click
from automated_proffast import automated_proffast_command_group


@click.group()
def cli() -> None:
    pass


cli.add_command(automated_proffast_command_group, name="automated-proffast")


if __name__ == "__main__":
    cli.main(prog_name="em27-pipeline-cli")
