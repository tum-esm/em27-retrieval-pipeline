import contextlib
import json
import re
from typing import Any, Generator, Optional
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
    os.path.join(PROJECT_DIR, "docs", "pages", "api-reference", "cli.mdx"), "w"
) as f:
    f.write("# CLI Reference\n\n")
    f.write(recursive_help(cli.cli))

# ---------------------------------------------------------
# EXPORT JSON SCHEMAS


def _remove_allof_wrapping(o: Any) -> Any:
    if isinstance(o, list):
        return [_remove_allof_wrapping(x) for x in o]
    elif isinstance(o, dict):
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
                **o["allOf"][0],
                **{k: v
                   for k, v in o.items() if k != "allOf"},
            }
        else:
            return {k: _remove_allof_wrapping(v) for k, v in o.items()}
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
# Replace metadata example files

example_metadata = em27_metadata.load_from_example_data()

with open(
    os.path.join(PROJECT_DIR, "docs", "pages", "api-reference", "metadata.mdx"),
    "r"
) as _f:
    current_metadata_reference = _f.read()

match1 = re.search(
    r"## `locations.json`\n\n### Example File\n\n```json[^`]+```",
    current_metadata_reference,
    flags=re.MULTILINE,
)
assert match1 is not None
current_metadata_reference = current_metadata_reference.replace(
    match1.group(0),
    "## `locations.json`\n\n### Example File\n\n```json\n" +
    example_metadata.locations.model_dump_json(indent=4) + "\n```",
)

match2 = re.search(
    r"## `sensors.json`\n\n### Example File\n\n```json[^`]+```",
    current_metadata_reference,
    flags=re.MULTILINE,
)
assert match2 is not None
current_metadata_reference = current_metadata_reference.replace(
    match2.group(0),
    "## `sensors.json`\n\n### Example File\n\n```json\n" +
    example_metadata.sensors.model_dump_json(indent=4) + "\n```",
)

match3 = re.search(
    r"## `campaigns.json`\n\n### Example File\n\n```json[^`]+```",
    current_metadata_reference,
    flags=re.MULTILINE,
)
assert match3 is not None
current_metadata_reference = current_metadata_reference.replace(
    match3.group(0),
    "## `campaigns.json`\n\n### Example File\n\n```json\n" +
    example_metadata.campaigns.model_dump_json(indent=4) + "\n```",
)

with open(
    os.path.join(PROJECT_DIR, "docs", "pages", "api-reference", "metadata.mdx"),
    "w"
) as _f:
    _f.write(current_metadata_reference)

# ---------------------------------------------------------
# Replace config example file

config_string = src.types.Config.load(
    tum_esm_utils.files.rel_to_abs_path(
        os.path.join(PROJECT_DIR, "config", "config.template.json")
    ),
    ignore_path_existence=True,
).model_dump_json(indent=4)

### reference

with open(
    os.path.join(
        PROJECT_DIR, "docs", "pages", "api-reference", "configuration.mdx"
    ), "r"
) as _f:
    current_config_reference = _f.read()

match4 = re.search(
    r"## `config.json`\n\n### Example File\n\n```json[^`]+```",
    current_config_reference,
    flags=re.MULTILINE,
)
assert match4 is not None
current_config_reference = current_config_reference.replace(
    match4.group(0),
    "## `config.json`\n\n### Example File\n\n```json\n" + config_string +
    "\n```",
)

with open(
    os.path.join(
        PROJECT_DIR, "docs", "pages", "api-reference", "configuration.mdx"
    ), "w"
) as _f:
    _f.write(current_config_reference)

### guide

with open(
    os.path.join(PROJECT_DIR, "docs", "pages", "guides", "configuration.mdx"),
    "r"
) as _f:
    current_config_guide = _f.read()

match5 = re.search(
    r"\nTemplate:\n\n```json[^`]+```",
    current_config_guide,
    flags=re.MULTILINE,
)
assert match5 is not None
current_config_guide = current_config_guide.replace(
    match5.group(0),
    "\nTemplate:\n\n```json\n" + config_string + "\n```",
)

with open(
    os.path.join(PROJECT_DIR, "docs", "pages", "guides", "configuration.mdx"),
    "w"
) as _f:
    _f.write(current_config_guide)

# ---------------------------------------------------------
# Sync README

with open(os.path.join(PROJECT_DIR, "docs", "pages", "index.mdx")) as _f:
    current_docs_landing_page = _f.read()

xs = current_docs_landing_page.split(
    'import { Callout } from "nextra/components";'
)
assert len(xs) == 2

with open(os.path.join(PROJECT_DIR, "README.md")) as _f:
    readme = _f.read()

with open(os.path.join(PROJECT_DIR, "docs", "pages", "index.mdx"), "w") as _f:
    _f.write(
        readme + '\n\nimport { Callout } from "nextra/components";' + xs[1]
    )
