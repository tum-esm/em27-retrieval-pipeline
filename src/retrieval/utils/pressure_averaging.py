import datetime
from typing import Any, Optional

import polars as pl
import skyfield.almanac  # pyright: ignore[reportMissingTypeStubs]
import skyfield.api  # pyright: ignore[reportMissingTypeStubs]
import skyfield.iokit  # pyright: ignore[reportMissingTypeStubs]
import tum_esm_utils

from .logger import Logger


def compute_solar_noon_time(
    lat: float,
    lon: float,
    date: datetime.date,
) -> datetime.datetime:
    start_time = datetime.datetime.combine(date, datetime.time.min, tzinfo=datetime.timezone.utc)
    end_time = start_time + datetime.timedelta(days=1)
    timescale = skyfield.api.load.timescale()  # pyright: ignore[reportUnknownMemberType]
    ephemeris: Any = skyfield.iokit.Loader(tum_esm_utils.files.rel_to_abs_path("../../../data"))(  # pyright: ignore[reportUnknownVariableType]
        "de421.bsp"
    )

    times, events = skyfield.almanac.find_discrete(  # type: ignore
        timescale.from_datetime(start_time),  # type: ignore
        timescale.from_datetime(end_time),  # type: ignore
        skyfield.almanac.meridian_transits(  # type: ignore
            ephemeris,
            ephemeris["Sun"],
            skyfield.api.wgs84.latlon(  # type: ignore
                latitude_degrees=lat,
                longitude_degrees=lon,
            ),
        ),
    )

    # Select transits instead of antitransits.
    t = times[events == 1][0].astimezone(datetime.timezone.utc)  # type: ignore
    assert isinstance(t, datetime.datetime)
    return t


def compute_mean_pressure_around_noon(
    solar_noon_datetime: datetime.datetime,
    filepath: str,
    logger: Optional[Logger] = None,
) -> float:
    df = pl.read_csv(
        filepath,
        schema_overrides={
            "utc-time": pl.Utf8,
            "pressure": pl.Float64,
        },
    ).with_columns(
        pl.col("utc-time").str.strptime(dtype=pl.Time, format="%H:%M:%S").alias("utc-time")
    )
    if logger is not None:
        logger.debug(f"Found {len(df)} pressure data points")
    df_around_noon = df.filter(
        (pl.col("utc-time") >= (solar_noon_datetime - datetime.timedelta(minutes=120)).time())
        & (pl.col("utc-time") <= (solar_noon_datetime + datetime.timedelta(minutes=120)).time())
    )
    if logger is not None:
        logger.debug(f"Found {len(df_around_noon)} pressure data points around noon (+- 2h)")
    assert len(df_around_noon) > 10, "Did not find enough pressure data around solar noon"
    return round(
        float(df_around_noon.select("pressure").drop_nulls().to_numpy().flatten().mean()), 3
    )
