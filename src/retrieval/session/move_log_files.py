import datetime
import os
import re
import polars as pl
from src import types, utils, retrieval


def run(
    config: types.Config,
    logger: retrieval.utils.logger.Logger,
    session: types.RetrievalSession,
) -> None:
    date_string = session.ctx.from_datetime.strftime("%Y%m%d")
    c = config.general.data.ground_pressure
    d = os.path.join(c.path.root, session.ctx.pressure_data_source)

    all_files = os.listdir(d)

    src_file_regex = utils.text.replace_regex_placeholders(
        c.file_regex, session.ctx.sensor_id, session.ctx.from_datetime.date()
    )
    src_file_pattern = re.compile(src_file_regex)
    matching_files = [f for f in all_files if src_file_pattern.match(f) is not None]
    assert len(matching_files) > 0, "no matching files found"

    logger.debug(f"Looking for files in {d} with regex {src_file_regex}")
    logger.debug(f"Found {len(all_files)} files in total and {len(matching_files)} matching files")

    datetimes: list[datetime.datetime] = []
    pressures: list[float] = []
    for file in matching_files:
        logger.debug(f"Parsing file {file}")
        df = pl.read_csv(os.path.join(d, file), has_header=True, separator=c.separator)

        multiplier = {
            "hPa": 1,
            "Pa": 0.01,
        }[c.pressure_column_format]
        assert c.pressure_column in df.columns, \
            "pressure column not found, found columns: " + (", ".join(df.columns))
        new_pressures = [float(p) * multiplier for p in df[c.pressure_column]]

        if c.datetime_column is not None:
            assert c.datetime_column_format is not None, "this is a bug in the pipeline"
            assert c.datetime_column in df.columns, \
                f"datetime column `{c.datetime_column}`not found, found columns: " + (", ".join(df.columns))

            new_datetimes = [
                datetime.datetime.strptime(d, c.datetime_column_format).astimezone(
                    datetime.timezone.utc
                ) for d in df[c.datetime_column]
            ]
            datetimes += new_datetimes
            pressures += new_pressures
        elif c.date_column:
            assert c.date_column_format is not None, "this is a bug in the pipeline"
            assert c.time_column is not None, "this is a bug in the pipeline"
            assert c.time_column_format is not None, "this is a bug in the pipeline"

            assert c.date_column in df.columns, \
                f"date column `{c.date_column}` not found, found columns: " + (", ".join(df.columns))
            assert c.time_column in df.columns, \
                f"time column `{c.time_column}` not found, found columns: " + (", ".join(df.columns))

            new_dates = [
                datetime.datetime.strptime(d, c.date_column_format) for d in df[c.date_column]
            ]
            new_times = [
                datetime.datetime.strptime(t, c.time_column_format) for t in df[c.time_column]
            ]
            new_datetimes = [
                datetime.datetime.combine(d.date(), t.time(), tzinfo=datetime.timezone.utc)
                for d, t in zip(new_dates, new_times)
            ]
            datetimes += new_datetimes
            pressures += new_pressures
        else:
            assert c.unix_timestamp_column is not None, "this is a bug in the pipeline"
            assert c.unix_timestamp_column_format is not None, "this is a bug in the pipeline"

            assert c.unix_timestamp_column in df.columns, \
                f"unix timestamp column `{c.unix_timestamp_column}` not found, found columns: " + (", ".join(df.columns))

            multiplier = {
                "s": 1,
                "ms": 1e-3,
                "us": 1e-6,
                "ns": 1e-9,
            }[c.unix_timestamp_column_format]
            new_datetimes = [
                datetime.datetime.fromtimestamp(t * multiplier, tz=datetime.timezone.utc)
                for t in df[c.unix_timestamp_column]
            ]
            datetimes += new_datetimes
            pressures += new_pressures

    df = pl.DataFrame({"utc": datetimes, "pressure": pressures})
    logger.debug(f"Found {len(df)} ground pressure records in total")

    # filter to the current day
    df = df.filter(pl.col("utc").dt.date().eq(session.ctx.from_datetime.date()))
    logger.debug(f"Reduced to {len(df)} records for the current day")

    # bin to 1s intervals
    df = df.sort("utc").group_by_dynamic("utc", every="1s").agg(
        pl.col("pressure").mean().alias("pressure")
    )
    logger.debug(f"Reduced to {len(df)} records after binning in 1s intervals")
    assert len(df) > 0, "no ground pressure records found for the current day"

    # write out file used for retrieval
    df.select(
        pl.col("utc").dt.strftime("%Y-%m-%d").alias("utc-date"),
        pl.col("utc").dt.strftime("%H:%M:%S").alias("utc-time"),
        pl.col("pressure"),
    ).write_csv(
        os.path.join(
            session.ctn.data_input_path, "log",
            f"ground-pressure-{session.ctx.pressure_data_source}-{date_string}.csv"
        )
    )
