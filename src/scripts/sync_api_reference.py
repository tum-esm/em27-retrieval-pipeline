import re
from typing import Optional
import shutil
import os
import sys
import click.core
import em27_metadata
import tum_esm_utils

_PROJECT_DIR = tum_esm_utils.files.rel_to_abs_path("../..")
_DOCS_DIR = os.path.join(_PROJECT_DIR, "docs")

sys.path.append(_PROJECT_DIR)
import cli
import src

# ---------------------------------------------------------
# EXPORT CLI REFERENCE

# credits to https://stackoverflow.com/a/58018765/8255842


def recursive_help(
    command: click.Group | click.Command,
    parent_context: Optional[click.core.Context] = None,
) -> str:
    output: str = ""
    context = click.core.Context(command, info_name=command.name, parent=parent_context)
    if isinstance(command, click.Group):
        for sub_command in command.commands.values():
            output += recursive_help(sub_command, parent_context=context)
    else:
        assert (
            command.short_help is not None
        ), f"Command {context.command_path} has no short help".format(command=command)
        output += f"## {command.short_help}\n\n"
        help_text = command.get_help(context)
        # find all options (--help)
        options: list[str] = re.findall(r"(\-\-\w[\w\-]+ )", help_text)
        for option in options:
            help_text = help_text.replace(option, f"\n`{option}`")
        output += (
            help_text.replace(
                "\n  ",
                "\n",
            )
            .replace(
                "[OPTIONS]",
                "",
            )
            .replace(
                f"Usage: {context.command_path}",
                f"**Usage:**\n\n`python cli.py {context.command_path[4:]} [OPTIONS]`\n\n**Description:** ",
            )
            .replace(
                "Options:\n",
                "**Options:**\n\n",
            )
            + "\n\n"
        )
    return output


print("Exporting CLI reference to docs/src/content/api-reference/cli.mdx")
with open(f"{_DOCS_DIR}/src/content/docs/api-reference/cli.mdx", "w") as f:
    f.write("---\ntitle: CLI Reference\n---\n\n")
    f.write(recursive_help(cli.cli))

# ---------------------------------------------------------
# EXPORT JSON SCHEMAS

print("Exporting JSON schemas to docs/src/assets")
tum_esm_utils.files.dump_json_file(
    f"{_DOCS_DIR}/src/assets/config.schema.json",
    src.types.Config.model_json_schema(mode="validation"),
)
tum_esm_utils.files.dump_json_file(
    f"{_DOCS_DIR}/src/assets/locations.schema.json",
    em27_metadata.types.LocationMetadataList.model_json_schema(mode="validation"),
)
tum_esm_utils.files.dump_json_file(
    f"{_DOCS_DIR}/src/assets/sensors.schema.json",
    em27_metadata.types.SensorMetadataList.model_json_schema(mode="validation"),
)
tum_esm_utils.files.dump_json_file(
    f"{_DOCS_DIR}/src/assets/campaigns.schema.json",
    em27_metadata.types.CampaignMetadataList.model_json_schema(mode="validation"),
)
tum_esm_utils.files.dump_json_file(
    f"{_DOCS_DIR}/src/assets/geoms-metadata.schema.json",
    src.types.GEOMSMetadata.model_json_schema(mode="validation"),
)
tum_esm_utils.files.dump_json_file(
    f"{_DOCS_DIR}/src/assets/calibration-factors.schema.json",
    src.types.CalibrationFactorsList.model_json_schema(mode="validation"),
)

# ---------------------------------------------------------
# COPY EXAMPLE FILES

print("Copying example files to docs/src/assets")
shutil.copyfile(
    f"{_PROJECT_DIR}/config/config.template.json",
    f"{_DOCS_DIR}/src/assets/config.example.json",
)
shutil.copyfile(
    f"{_PROJECT_DIR}/config/geoms_metadata.template.json",
    f"{_DOCS_DIR}/src/assets/geoms-metadata.example.json",
)
shutil.copyfile(
    f"{_PROJECT_DIR}/config/calibration_factors.template.json",
    f"{_DOCS_DIR}/src/assets/calibration-factors.example.json",
)
example_metadata = em27_metadata.load_from_example_data()
tum_esm_utils.files.dump_file(
    f"{_DOCS_DIR}/src/assets/locations.example.json",
    example_metadata.locations.model_dump_json(indent=4),
)
tum_esm_utils.files.dump_file(
    f"{_DOCS_DIR}/src/assets/sensors.example.json",
    example_metadata.sensors.model_dump_json(indent=4),
)
tum_esm_utils.files.dump_file(
    f"{_DOCS_DIR}/src/assets/campaigns.example.json",
    example_metadata.campaigns.model_dump_json(indent=4),
)

# --------------------------------------------------------
# Sync README

print("Syncing README with docs landing page")

current = tum_esm_utils.files.load_file(f"{_DOCS_DIR}/src/content/docs/index.mdx")

a = current.split("We retrieve a lot of ")[0]
b = current.split("We retrieve a lot of ")[1].split("##")[0]
c = "##".join(current.split("We retrieve a lot of ")[1].split("##")[1:])

readme = tum_esm_utils.files.load_file(os.path.join(_PROJECT_DIR, "README.md")).split(
    "We retrieve a lot of "
)[1]

tum_esm_utils.files.dump_file(
    f"{_DOCS_DIR}/src/content/docs/index.mdx",
    f"{a}We retrieve a lot of {readme}\n##{c}",
)
