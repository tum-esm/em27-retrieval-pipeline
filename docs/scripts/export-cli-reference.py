from typing import Optional
import tum_esm_utils
import sys
import click.core

PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=3)
sys.path.append(PROJECT_DIR)
import cli

# credits to https://stackoverflow.com/a/58018765/8255842


def recursive_help(
    command: click.Group | click.Command,
    parent_context: Optional[click.core.Context] = None,
) -> str:
    output: str = ""
    context = click.core.Context(
        command, info_name=command.name, parent=parent_context
    )
    if isinstance(command, click.Group):
        for sub_command in command.commands.values():
            output += recursive_help(sub_command, parent_context=context)
    else:
        output += f"## `{context.command_path[4:]}`\n\n"
        output += command.get_help(context).replace(
            "\n  ",
            "\n",
        ).replace(
            f"Usage: {context.command_path}",
            f"**Usage: python cli.py {context.command_path[4:]}",
        ).replace(
            "[OPTIONS]",
            "[OPTIONS]**",
        ).replace(
            "Options:\n",
            "**Options:**\n\n",
        ) + "\n\n"
    return output


with open("a.md", "w") as f:
    f.write("# CLI Reference\n\n")
    f.write(recursive_help(cli.cli))
