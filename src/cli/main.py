import click
from proffast import proffast_command_group


@click.group()
def cli() -> None:
    pass


cli.add_command(proffast_command_group, name="proffast")


if __name__ == "__main__":
    cli.main(prog_name="em27-pipeline-cli")
