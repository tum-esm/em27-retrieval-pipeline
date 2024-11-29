import os

import polars as pl

from src import retrieval, types


def run(
    config: types.Config,
    logger: retrieval.utils.logger.Logger,
    session: types.RetrievalSession,
) -> None:
    date_string = session.ctx.from_datetime.strftime("%Y%m%d")
    c = config.general.data.ground_pressure
    d = os.path.join(c.path.root, session.ctx.pressure_data_source)
    assert os.path.exists(d), f"directory {d} does not exist"

    all_files, compatible_files, matching_files = (
        retrieval.utils.pressure_loading.find_pressure_files(
            c.path.root,
            session.ctx.pressure_data_source,
            c.file_regex,
            session.ctx.from_datetime.date(),
        )
    )
    logger.debug(f"Looking for files in {d} with regex {c.file_regex}")
    logger.debug(f"Found {len(all_files)} files in total")
    logger.debug(f"Found {len(compatible_files)} files that match the regex")
    logger.debug(f"Found {len(matching_files)} files that match the regex on that date")

    assert len(matching_files) > 0, "No matching files found"

    dataframes: list[pl.DataFrame] = []
    for file in matching_files:
        logger.debug(f"Parsing file {file}")
        dataframes.append(
            retrieval.utils.pressure_loading.load_pressure_file(c, os.path.join(d, file))
        )

    df = pl.concat(dataframes)
    logger.debug(f"Found {len(df)} ground pressure records in total")

    # filter to the current day
    df = df.filter(pl.col("utc").dt.date().eq(session.ctx.from_datetime.date()))
    logger.debug(f"Reduced to {len(df)} records for the current day")

    # bin to 1s intervals
    df = (
        df.sort("utc")
        .group_by_dynamic("utc", every="1s")
        .agg(pl.col("pressure").mean().alias("pressure"))
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
            session.ctn.data_input_path,
            "log",
            f"ground-pressure-{session.ctx.pressure_data_source}-{date_string}.csv",
        )
    )
