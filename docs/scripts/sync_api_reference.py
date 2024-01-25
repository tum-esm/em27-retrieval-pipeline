import json
import re
from typing import Any, Optional
import os
import em27_metadata
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


def _remove_allof_wrapping(o: dict[str, Any]) -> dict[str, Any]:
    if "properties" in o.keys():
        return {
            **o,
            "properties": {
                k: _remove_allof_wrapping(v)
                for k, v in o["properties"].items()
            },
        }
    elif "allOf" in o.keys():
        assert len(o["allOf"]) == 1
        return {
            **{k: v
               for k, v in o.items() if k != "allOf"},
            **o["allOf"][0],
        }
    else:
        return o


def export_schema(src_object: Any, dst_filepath: str, label: str) -> None:
    print(f"Exporting schema object to {dst_filepath}")

    # remove $ref usages
    schema_without_refs = jsonref.loads(
        json.dumps(src_object.model_json_schema(by_alias=False))
    )

    # remove $defs section
    schema_without_defs = json.loads(
        jsonref.dumps(schema_without_refs, indent=4)
    )
    if "$defs" in schema_without_defs.keys():
        del schema_without_defs["$defs"]

    # convert weird "allOf" wrapping to normal wrapping
    schema_without_allofs = _remove_allof_wrapping(schema_without_defs)

    # write out file
    with open(dst_filepath, "w") as f:
        f.write(
            f"/* prettier-ignore */\nconst {label}: any = " +
            json.dumps(schema_without_allofs, indent=4) +
            f";\n\nexport default {label};"
        )


COMPONENTS_DIR = os.path.join(PROJECT_DIR, "docs", "components")
export_schema(
    src.types.Config,
    os.path.join(COMPONENTS_DIR, "config-schema.ts"),
    "CONFIG_SCHEMA",
)
export_schema(
    em27_metadata.types.LocationMetadataList,
    os.path.join(COMPONENTS_DIR, "locations-schema.ts"),
    "LOCATIONS_SCHEMA",
)
export_schema(
    em27_metadata.types.SensorMetadataList,
    os.path.join(COMPONENTS_DIR, "sensors-schema.ts"),
    "SENSORS_SCHEMA",
)
export_schema(
    em27_metadata.types.CampaignMetadataList,
    os.path.join(COMPONENTS_DIR, "campaigns-schema.ts"),
    "CAMPAIGNS_SCHEMA",
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
