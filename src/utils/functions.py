import datetime
import os
from typing import Any, Optional
import polars as pl
import em27_metadata
import tum_esm_utils

try:
    import tomllib  # type: ignore
except ImportError:
    import tomli as tomllib  # type: ignore


def sdc_covers_the_full_day(
    sdc: em27_metadata.types.SensorDataContext,
) -> bool:
    return (
        sdc.from_datetime.time().replace(microsecond=0) == datetime.time.min.replace(microsecond=0)
    ) and (
        sdc.to_datetime.time().replace(microsecond=0) == datetime.time.max.replace(microsecond=0)
    )


def get_pipeline_version() -> str:
    """Returns the current version (`x.y.z`) of the pipeline."""

    with open(tum_esm_utils.files.rel_to_abs_path("../../pyproject.toml"), "rb") as f:
        try:
            v: Any = tomllib.load(f)["project"]["version"]  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
            assert isinstance(v, str)
            return v
        except (KeyError, AssertionError):
            raise ValueError("Could not find project version in `pyproject.toml`")


def load_dat_file(
    filepath: str,
    possible_separators: list[str] = ["!", "?", "&"],
) -> pl.DataFrame:
    """Loads a `.dat` file as a Polars DataFrame.

    The separator should be a character that does not occur in the file itself."""

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    filecontent = tum_esm_utils.files.load_file(filepath)
    separator: Optional[str] = None
    for s in possible_separators:
        if s not in filecontent:
            separator = s
            break
    if separator is None:
        raise ValueError(f"All possible separators occur in the file: {possible_separators}")

    columns = [
        c
        for c in filecontent.split("\n")[0].replace(",", " ").replace("\t", " ").split(" ")
        if c != ""
    ]
    return (
        pl.read_csv(filepath, new_columns=["full"], separator=separator)
        .with_columns(
            pl.col("full")
            .str.replace_all(",", " ")
            .str.split(" ")
            .list.filter(pl.element().str.len_chars().gt(0))
            .alias("splitted")
        )
        .with_columns(
            [
                pl.col("splitted").list.get(i).str.strip_chars(" ").alias(columns[i])
                for i in range(len(columns))
            ]
        )
        .drop("full", "splitted")
    )
