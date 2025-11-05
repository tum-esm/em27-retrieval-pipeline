import datetime
import os

import polars as pl

from src import types, utils


def find_pressure_files(
    root_dir: str,
    sensor_id: str,
    file_regex: str,
    date: datetime.date,
) -> tuple[list[str], list[str], list[str]]:
    """Find pressure files for a given sensor and date.

    Returns: tuple[list of all files for that sensor, list of all files following the given pattern, list of all matching files for that date]"""

    d = os.path.join(root_dir, sensor_id)
    if not os.path.exists(d):
        return [], [], []

    all_files = sorted(os.listdir(d))

    general_file_pattern, specific_file_pattern = utils.text.replace_regex_placeholders(
        file_regex, sensor_id, date
    )

    general_matching_files = [f for f in all_files if general_file_pattern.match(f) is not None]
    specific_matching_files = [f for f in all_files if specific_file_pattern.match(f) is not None]

    return all_files, general_matching_files, specific_matching_files


def pressure_files_exist(
    root_dir: str,
    sensor_id: str,
    file_regex: str,
    date: datetime.date,
) -> bool:
    """Check if pressure files for a given sensor and date exist. Like `find_pressure_files`, but more efficient. Use in the retrieval queue.

    Returns: bool indicating if any matching files exist."""

    d = os.path.join(root_dir, sensor_id)
    try:
        _, specific_file_pattern = utils.text.replace_regex_placeholders(
            file_regex, sensor_id, date
        )
        return any([specific_file_pattern.match(f) is not None for f in os.listdir(d)])
    except FileNotFoundError:
        return False


def load_pressure_file(
    ground_pressure_config: types.config.GroundPressureConfig,
    filepath: str,
) -> pl.DataFrame:
    c = ground_pressure_config
    df = pl.read_csv(
        filepath,
        has_header=True,
        separator=c.separator,
        schema_overrides={
            k: v
            for k, v in {
                c.datetime_column: pl.Utf8,
                c.date_column: pl.Utf8,
                c.time_column: pl.Utf8,
                c.unix_timestamp_column: pl.Float64,
                c.pressure_column: pl.Float64,
            }.items()
            if k is not None
        },
    )

    # remove all rows with missing pressure/datetime information
    # the other columns are allowed to have nulls
    for column_name, label in [
        (c.pressure_column, "pressure"),
        (c.datetime_column, "datetime"),
        (c.date_column, "date"),
        (c.time_column, "time"),
        (c.unix_timestamp_column, "unix timestamp"),
    ]:
        if column_name is not None:
            assert column_name in df.columns, (
                f"{label} column not found, found columns: {df.columns} "
            )
            df = df.drop_nulls(column_name)

    # LOAD PRESSURE

    custom_unit_to_hpa: float
    if c.pressure_column_format == "hPa":
        custom_unit_to_hpa = 1
    elif c.pressure_column_format == "Pa":
        custom_unit_to_hpa = 0.01
    elif c.pressure_column_format == "bar":
        custom_unit_to_hpa = 1000
    elif c.pressure_column_format == "mbar":
        custom_unit_to_hpa = 1
    elif c.pressure_column_format == "atm":
        custom_unit_to_hpa = 1013.25
    elif c.pressure_column_format == "psi":
        custom_unit_to_hpa = 68.9476
    elif c.pressure_column_format == "inHg":
        custom_unit_to_hpa = 33.8639
    elif c.pressure_column_format == "mmHg":
        custom_unit_to_hpa = 1.33322
    else:
        raise Exception("This should not happen")

    pressures = [
        float(p)
        for p in df.select(pl.col(c.pressure_column).mul(custom_unit_to_hpa))[c.pressure_column]
    ]
    datetimes: list[datetime.datetime]

    # PARSE DATETIME COLUMN
    if c.datetime_column is not None:
        assert c.datetime_column_format is not None, "this is a bug in the pipeline"
        datetimes = []
        for d in df[c.datetime_column]:
            try:
                datetimes.append(
                    datetime.datetime.strptime(d, c.datetime_column_format).astimezone(
                        datetime.timezone.utc
                    )
                )
            except ValueError:
                raise ValueError(
                    f"datetime `{d}` does not match format `{c.datetime_column_format}`"
                )

    # PARSE DATE AND TIME COLUMNS
    elif c.date_column:
        assert c.date_column_format is not None, "this is a bug in the pipeline"
        assert c.time_column is not None, "this is a bug in the pipeline"
        assert c.time_column_format is not None, "this is a bug in the pipeline"

        dates: list[datetime.date] = []
        for d in df[c.date_column]:
            try:
                dates.append(datetime.datetime.strptime(d, c.date_column_format).date())
            except ValueError:
                raise ValueError(f"date `{d}` does not match format `{c.date_column_format}`")
        times: list[datetime.time] = []
        for t in df[c.time_column]:
            try:
                times.append(datetime.datetime.strptime(t, c.time_column_format).time())
            except ValueError:
                raise ValueError(f"time `{t}` does not match format `{c.time_column_format}`")

        datetimes = [
            datetime.datetime.combine(d, t, tzinfo=datetime.timezone.utc)
            for d, t in zip(dates, times)
        ]

    # PARSE UNIX TIMESTAMP COLUMN
    else:
        assert c.unix_timestamp_column is not None, "this is a bug in the pipeline"
        assert c.unix_timestamp_column_format is not None, "this is a bug in the pipeline"

        custom_unit_to_seconds: float
        if c.unix_timestamp_column_format == "s":
            custom_unit_to_seconds = 1
        elif c.unix_timestamp_column_format == "ms":
            custom_unit_to_seconds = 1e-3
        elif c.unix_timestamp_column_format == "us":
            custom_unit_to_seconds = 1e-6
        elif c.unix_timestamp_column_format == "ns":
            custom_unit_to_seconds = 1e-9
        else:
            raise Exception("This should not happen")

        datetimes = []
        for t in df[c.unix_timestamp_column]:
            try:
                datetimes.append(
                    datetime.datetime.fromtimestamp(
                        t * custom_unit_to_seconds, tz=datetime.timezone.utc
                    )
                )
            except ValueError:
                raise ValueError(f"unix timestamp `{t}` could not be converted to a datetime")

    return pl.DataFrame({"utc": datetimes, "pressure": pressures}).sort("utc")
