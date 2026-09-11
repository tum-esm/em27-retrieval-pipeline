import os
import re
import shutil
import sys
import copy
from typing import Any, Optional
import click
import tum_esm_utils.files

sys.path.append(tum_esm_utils.files.rel_to_abs_path(".."))

import src
import cli

PROJECT_DIR = tum_esm_utils.files.rel_to_abs_path("..")


def simplify_anyof_nullable(schema: Any) -> Any:
    """
    Recursively simplify JSON Schema fragments like:

        {"anyOf": [{"type": "string", ...}, {"type": "null"}], ...}

    into:

        {"type": "string", "nullable": true, ...}

    Rules:
    - Only simplifies `anyOf` if there is exactly one non-null branch.
    - Copies inner keys from the non-null branch to the outer object.
    - Outer keys win if there is a conflict.
    - Outer `description` is never overwritten.
    - Adds `"nullable": true` if one of the branches is `{"type": "null"}`.
    """
    if isinstance(schema, list):
        return [simplify_anyof_nullable(item) for item in schema]

    if not isinstance(schema, dict):
        return schema

    # First recurse into children
    schema = {k: simplify_anyof_nullable(v) for k, v in schema.items()}

    anyof = schema.get("anyOf")
    if isinstance(anyof, list):
        non_null_options = []
        has_null = False

        for option in anyof:
            if isinstance(option, dict) and option.get("type") == "null":
                has_null = True
            else:
                non_null_options.append(option)

        if len(non_null_options) == 1 and isinstance(non_null_options[0], dict):
            inner = copy.deepcopy(non_null_options[0])

            # Remove anyOf from outer before merging
            schema.pop("anyOf", None)

            # Merge inner keys into outer, but do not overwrite outer keys
            for key, value in inner.items():
                if key == "description" and "description" in schema:
                    continue
                if key not in schema:
                    schema[key] = value

            if has_null:
                schema["nullable"] = True

    return schema


def simplify_enum_nullable(schema: Any) -> Any:
    """
    Recursively simplify JSON Schema fragments like:

        {"enum": ["a", "b", null], ...}

    into:

        {"enum": ["a", "b", null], "type": "string", "nullable": true, ...}

    Rules:
    - Only simplifies `enum` if values contain `null` and all non-null values
      are of exactly one JSON type.
    - Adds `"type"` only if it does not already exist.
    - Adds `"nullable": true` when `null` is part of the enum.
    """
    if isinstance(schema, list):
        return [simplify_enum_nullable(item) for item in schema]

    if not isinstance(schema, dict):
        return schema

    # First recurse into children
    schema = {k: simplify_enum_nullable(v) for k, v in schema.items()}

    enum_values = schema.get("enum")
    if not isinstance(enum_values, list):
        return schema

    has_null = any(v is None for v in enum_values)
    if not has_null:
        return schema

    non_null_values = [v for v in enum_values if v is not None]
    if not non_null_values:
        return schema

    def json_type(value: Any) -> str:
        # bool is a subclass of int in Python, so detect it first.
        if isinstance(value, bool):
            return "boolean"
        if isinstance(value, int):
            return "integer"
        if isinstance(value, float):
            return "number"
        if isinstance(value, str):
            return "string"
        if isinstance(value, list):
            return "array"
        if isinstance(value, dict):
            return "object"
        return "unknown"

    types = {json_type(v) for v in non_null_values}
    if len(types) != 1 or "unknown" in types:
        return schema

    if "type" not in schema:
        schema["type"] = types.pop()
    schema["nullable"] = True
    return schema


def normalize_schema(schema: Any) -> Any:
    schema = simplify_anyof_nullable(schema)
    schema = simplify_enum_nullable(schema)
    return schema


# export schemas

tum_esm_utils.files.dump_json_file(
    f"{PROJECT_DIR}/docs/src/assets/config.schema.json",
    normalize_schema(
        src.types.Config.model_json_schema(
            mode="serialization",
            union_format="primitive_type_array",
        )
    ),
    indent=4,
)
tum_esm_utils.files.dump_json_file(
    f"{PROJECT_DIR}/docs/src/assets/em27_metadata.schema.json",
    normalize_schema(
        src.em27_metadata.types.EM27MetadataObject.model_json_schema(
            mode="serialization",
            union_format="any_of",
        )
    ),
    indent=4,
)
tum_esm_utils.files.dump_json_file(
    f"{PROJECT_DIR}/docs/src/assets/geoms_metadata.schema.json",
    normalize_schema(
        src.types.GEOMSMetadata.model_json_schema(
            mode="serialization",
            union_format="primitive_type_array",
        )
    ),
    indent=4,
)

# export examples

for l in [
    "config.template.toml",
    "em27_metadata.template.toml",
    "geoms_metadata.template.toml",
]:
    shutil.copyfile(
        f"{PROJECT_DIR}/config/{l}",
        f"{PROJECT_DIR}/docs/src/assets/{l}",
    )

# sync index.mdx to README.md

print("Syncing README with docs landing page")

current = tum_esm_utils.files.load_file(f"{PROJECT_DIR}/docs/src/content/docs/index.mdx")

a = current.split("We retrieve a lot of ")[0]
b = (
    tum_esm_utils.files.load_file(f"{PROJECT_DIR}/README.md")
    .split("We retrieve a lot of ")[1]
    .replace("docs/public/images/", "images/")
    .replace("https://tum-esm.github.io/em27-retrieval-pipeline/guides", "/guides")
    .replace("https://tum-esm.github.io/em27-retrieval-pipeline/api-reference", "/api-reference")
)

tum_esm_utils.files.dump_file(
    f"{PROJECT_DIR}/docs/src/content/docs/index.mdx",
    f"{a}We retrieve a lot of {b}",
)


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
        assert command.short_help is not None, (
            f"Command {context.command_path} has no short help".format(command=command)
        )
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
with open(f"{PROJECT_DIR}/docs/src/content/docs/api-reference/cli.mdx", "w") as f:
    f.write("---\ntitle: CLI Reference\n---\n\n")
    f.write(recursive_help(cli.cli))
