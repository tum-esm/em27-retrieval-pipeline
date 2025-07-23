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
        output += f"## `{context.command_path[4:]}`\n\n"
        output += (
            command.get_help(context)
            .replace(
                "\n  ",
                "\n",
            )
            .replace(
                f"Usage: {context.command_path}",
                f"**Usage: python cli.py {context.command_path[4:]}",
            )
            .replace(
                "[OPTIONS]",
                "[OPTIONS]**",
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
    f"{_DOCS_DIR}/src/assets/geom-metadata.schema.json",
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
    f"{_DOCS_DIR}/src/assets/geoms_metadata.example.json",
)
shutil.copyfile(
    f"{_PROJECT_DIR}/config/calibration_factors.template.json",
    f"{_DOCS_DIR}/src/assets/calibration_factors.example.json",
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

xs = current.split("##")
assert len(xs) >= 2

readme = tum_esm_utils.files.load_file(os.path.join(_PROJECT_DIR, "README.md"))

tum_esm_utils.files.dump_file(
    f"{_DOCS_DIR}/src/content/docs/index.mdx",
    readme + "\n##" + "##".join(xs[1:]),
)
