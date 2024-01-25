import datetime
import tomllib
from typing import Any
import em27_metadata
import skyfield.iokit
import skyfield.api
import skyfield.timelib
import skyfield.almanac
import tum_esm_utils


def sdc_covers_the_full_day(
    sdc: em27_metadata.types.SensorDataContext,
) -> bool:
    return ((
        sdc.from_datetime.time().replace(microsecond=0)
        == datetime.time.min.replace(microsecond=0)
    ) and (
        sdc.to_datetime.time().replace(microsecond=0)
        == datetime.time.max.replace(microsecond=0)
    ))


def get_pipeline_version() -> str:
    """Returns the current version (`x.y.z`) of the pipeline."""

    with open(
        tum_esm_utils.files.rel_to_abs_path("../../pyproject.toml"), "rb"
    ) as f:
        try:
            v = tomllib.load(f)["project"]["version"]
            assert isinstance(v, str)
            return v
        except (KeyError, AssertionError):
            raise ValueError(
                "Could not find project version in `pyproject.toml`"
            )


def compute_solar_noon_time(
    lat: float,
    lon: float,
    date: datetime.date,
) -> datetime.datetime:
    start_time = datetime.datetime.combine(
        date, datetime.time.min, tzinfo=datetime.UTC
    )
    end_time = start_time + datetime.timedelta(days=1)
    timescale = skyfield.api.load.timescale()
    ephemeris: Any = skyfield.iokit.Loader(
        tum_esm_utils.files.rel_to_abs_path("../../data")
    )('de421.bsp')

    times, events = skyfield.almanac.find_discrete(
        timescale.from_datetime(start_time),
        timescale.from_datetime(end_time),
        skyfield.almanac.meridian_transits(
            ephemeris, ephemeris['Sun'],
            skyfield.api.wgs84.latlon(
                latitude_degrees=lat,
                longitude_degrees=lon,
            )
        ),
    )

    # Select transits instead of antitransits.
    t = times[events == 1][0].astimezone(datetime.UTC)
    assert isinstance(t, datetime.datetime)
    return t
