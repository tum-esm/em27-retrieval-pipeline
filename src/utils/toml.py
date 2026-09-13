from __future__ import annotations

from collections.abc import Collection, Mapping
from typing import cast

import tomli
import tomli_w


def _datetime_fields_first(value: object) -> object:
    """Recursively move datetime boundary fields to the start of each mapping.

    Args:
        value: TOML-compatible value to reorder. Lists and mappings are traversed;
            scalar values are returned unchanged.

    Returns:
        A reordered copy of each encountered list or mapping, with
        ``from_datetime`` and ``to_datetime`` first when present.
    """
    if isinstance(value, Mapping):
        mapping = cast(Mapping[str, object], value)
        ordered: dict[str, object] = {}
        for key in ("from_datetime", "to_datetime"):
            if key in mapping:
                ordered[key] = _datetime_fields_first(mapping[key])
        for key, item in mapping.items():
            if key not in ordered:
                ordered[key] = _datetime_fields_first(item)
        return ordered
    if isinstance(value, list):
        return [_datetime_fields_first(item) for item in cast(list[object], value)]
    return value


def _remove_empty_mappings(value: object) -> object:
    """Recursively remove mapping fields whose mappings are empty.

    Args:
        value: TOML-compatible value to clean. Lists and mappings are traversed;
            scalar values are returned unchanged.

    Returns:
        A copy of the value without fields containing empty mappings.
    """
    if isinstance(value, Mapping):
        mapping = cast(Mapping[str, object], value)
        cleaned: dict[str, object] = {}
        for key, item in mapping.items():
            cleaned_item = _remove_empty_mappings(item)
            if isinstance(cleaned_item, Mapping) and not cleaned_item:
                continue
            cleaned[key] = cleaned_item
        return cleaned
    if isinstance(value, list):
        return [_remove_empty_mappings(item) for item in cast(list[object], value)]
    return value


def _template_comments(template: str) -> dict[str, list[str]]:
    """Associate template comment dividers with their following root keys.

    Args:
        template: Complete TOML template text from which to read comments and
            root-level section names.

    Returns:
        Comment lines keyed by the root key whose section they introduce.
    """
    comments: dict[str, list[str]] = {}
    pending: list[str] = []
    for line in template.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            pending.append(stripped)
            continue
        if not stripped:
            continue
        if pending:
            if stripped.startswith("["):
                root_key = stripped.strip("[]").split(".", maxsplit=1)[0]
            else:
                root_key = stripped.split("=", maxsplit=1)[0].strip()
            comments.setdefault(root_key, pending)
        pending = []
    return comments


def _inline_sensor_deployments(toml: str) -> str:
    """Replace sensor deployment sub-tables with an array of inline tables.

    Args:
        toml: Serialized TOML containing ``[[sensors.deployments]]`` tables.

    Returns:
        The TOML text with each sensor's deployments represented by a compact
        ``deployments`` array containing one inline table per deployment.
    """
    lines = toml.splitlines()
    output: list[str] = []
    i = 0
    deployment_header = "[[sensors.deployments]]"
    while i < len(lines):
        if lines[i] != deployment_header:
            output.append(lines[i])
            i += 1
            continue

        if output and not output[-1]:
            output.pop()
        deployments: list[str] = []
        while i < len(lines) and lines[i] == deployment_header:
            i += 1
            fields: list[str] = []
            while i < len(lines) and lines[i] and not lines[i].startswith("["):
                fields.append(lines[i].strip())
                i += 1
            deployments.append("    { " + ", ".join(fields) + " }")
            while i < len(lines) and not lines[i]:
                i += 1

        output.append("deployments = [")
        output.extend(
            deployment + ("," if index < len(deployments) - 1 else "")
            for index, deployment in enumerate(deployments)
        )
        output.append("]")
        if i < len(lines):
            output.append("")
    return "\n".join(output)


def _inline_array_fields(
    toml: str, field_names: Collection[str] | None = None
) -> str:
    """Render selected multiline arrays as compact single-line arrays.

    Args:
        toml: Serialized TOML containing arrays to compact.
        field_names: Field names whose arrays should be rendered on one line.
            If omitted, every multiline array is rendered on one line.

    Returns:
        The TOML text with matching arrays formatted as ``[ value, value ]``.
    """
    lines = toml.splitlines()
    output: list[str] = []
    i = 0
    while i < len(lines):
        stripped_line = lines[i].strip()
        is_array = stripped_line.endswith(" = [")
        field_name = stripped_line.removesuffix(" = [")
        if not is_array or (field_names is not None and field_name not in field_names):
            output.append(lines[i])
            i += 1
            continue

        closing_bracket_index = i + 1
        values: list[str] = []
        while (
            closing_bracket_index < len(lines)
            and lines[closing_bracket_index].strip() != "]"
        ):
            values.append(lines[closing_bracket_index].strip().removesuffix(","))
            closing_bracket_index += 1
        if closing_bracket_index == len(lines):
            output.append(lines[i])
            i += 1
            continue

        indentation = lines[i][: len(lines[i]) - len(lines[i].lstrip())]
        output.append(f"{indentation}{field_name} = [ {', '.join(values)} ]")
        i = closing_bracket_index + 1
    return "\n".join(output)


def dump_pretty_toml_file(
    filepath: str,
    data: Mapping[str, object],
    template_filepath: str,
    inline_sensor_deployments: bool = False,
    inline_metadata_id_lists: bool = False,
    inline_all_lists: bool = False,
    omit_empty_tables: bool = False,
    omittable_empty_root_arrays: Collection[str] = (),
) -> None:
    """Write TOML using the ordering and section dividers of a template.

    Root keys are ordered like the template, unknown root keys are appended,
    and ``from_datetime``/``to_datetime`` fields are moved before other fields
    in nested objects. Empty root arrays that cannot be omitted are written
    before tables so that they remain at the TOML root.

    Args:
        filepath: Destination path for the generated TOML file.
        data: TOML-compatible root mapping to serialize.
        template_filepath: Path to the TOML template providing root-key order
            and comment dividers.
        inline_sensor_deployments: Whether to render sensor deployments as an
            array of inline tables instead of ``[[sensors.deployments]]``.
        inline_metadata_id_lists: Whether to render ``sensor_ids`` and
            ``location_ids`` arrays on one line in campaign and event sections.
        inline_all_lists: Whether to render every scalar list on one line.
        omit_empty_tables: Whether to recursively remove mapping fields that
            would otherwise produce empty TOML tables.
        omittable_empty_root_arrays: Root array keys that may be omitted when
            empty. Their comment divider is retained when the template has one.
    """
    with open(template_filepath, "r", encoding="utf-8") as file:
        template_text = file.read()
    with open(template_filepath, "rb") as file:
        template_data = cast(Mapping[str, object], tomli.load(file))

    output_data = (
        cast(Mapping[str, object], _remove_empty_mappings(data))
        if omit_empty_tables
        else data
    )
    root_keys = [key for key in template_data if key in output_data]
    root_keys.extend(key for key in output_data if key not in root_keys)
    comments = _template_comments(template_text)

    # TOML has no syntax for returning to the root after opening a table, so
    # required empty root arrays must appear before the sectioned content.
    required_empty_arrays = [
        key
        for key in root_keys
        if output_data[key] == [] and key not in omittable_empty_root_arrays
    ]
    chunks: list[str] = []
    for key in required_empty_arrays:
        chunk = tomli_w.dumps({key: []}).strip()
        if key in comments:
            chunk = "\n".join([*comments[key], "", chunk])
        chunks.append(chunk)
    for key in root_keys:
        if key in required_empty_arrays:
            continue
        if output_data[key] == []:
            if key in comments:
                chunks.append("\n".join(comments[key]))
            continue
        chunk = tomli_w.dumps({key: _datetime_fields_first(output_data[key])}).strip()
        if inline_sensor_deployments and key == "sensors":
            chunk = _inline_sensor_deployments(chunk)
        if inline_all_lists:
            chunk = _inline_array_fields(chunk)
        elif inline_metadata_id_lists and key in {"campaigns", "events"}:
            chunk = _inline_array_fields(chunk, ("sensor_ids", "location_ids"))
        if key in comments:
            chunk = "\n".join([*comments[key], "", chunk])
        chunks.append(chunk)

    with open(filepath, "w", encoding="utf-8", newline="\n") as file:
        file.write("\n\n".join(chunks) + "\n")
