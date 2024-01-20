import json
import re
from typing import Optional
import os
import tum_esm_utils
import sys
import jsonref
import click.core

PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=3)
sys.path.append(PROJECT_DIR)
import src, cli

# ---------------------------------------------------------
# EXPORT CLI REFERENCE

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


with open(
    os.path.join(
        PROJECT_DIR, "docs", "pages", "docs", "api-reference", "cli.mdx"
    ), "w"
) as f:
    f.write("# CLI Reference\n\n")
    f.write(recursive_help(cli.cli))

# ---------------------------------------------------------
# EXPORT JSON SCHEMAS

CONFIG_JSON_TARGET = os.path.join(
    PROJECT_DIR, "docs", "components", "config-schema-object.ts"
)
MANUAL_QUEUE_JSON_TARGET = os.path.join(
    PROJECT_DIR, "docs", "components", "manual-queue-schema-object.ts"
)
MD_FILE_TARGET = os.path.join(
    PROJECT_DIR, "docs", "pages", "docs", "api-reference",
    "configuration-files.mdx"
)
sys.path.append(PROJECT_DIR)

# ---------------------------------------------------------
# Update the config schema object in the documentation

config_schema_str = json.dumps(src.types.Config.model_json_schema(), indent=2)
dereferenced_config_schema = jsonref.loads(config_schema_str)
with open(CONFIG_JSON_TARGET, "w") as f:
    f.write(
        "/* prettier-ignore */\n" + "const CONFIG_SCHEMA_OBJECT: any = " +
        json.dumps(dereferenced_config_schema, indent=2) +
        ";\n\nexport default CONFIG_SCHEMA_OBJECT;"
    )

# ---------------------------------------------------------
# Update the example files in the documentation
"""
TODO: renew this

with open(MD_FILE_TARGET) as f:
    md_file_content = f.read()

example_file_blocks = re.findall(
    r"Example File\n\n```[\s\S]*?```", md_file_content
)
assert len(example_file_blocks) == 2
assert len(example_file_blocks[0]) > len(example_file_blocks[1])

with open(os.path.join(PROJECT_DIR, "config", "config.template.json")) as f:
    config_template_content = f.read()

md_file_content = md_file_content.replace(
    example_file_blocks[0],
    f"Example File\n\n```json\n{config_template_content.strip()}\n```",
)
md_file_content = md_file_content.replace(
    example_file_blocks[1],
    f"Example File\n\n```json\n{manual_queue_template_content.strip()}\n```",
)

with open(MD_FILE_TARGET, "w") as f:
    f.write(md_file_content)
"""
