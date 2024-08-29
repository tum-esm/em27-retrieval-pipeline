import datetime
import os
import random
import pytest
import tum_esm_utils
import src
from ..fixtures import download_sample_data

_DATALOGGER_DIR = tum_esm_utils.files.rel_to_abs_path(
    "../../data/testing/container/inputs/log/"
)


@pytest.mark.order(3)
@pytest.mark.quick
def test_solar_noon_computation() -> None:
    start_date = datetime.date(2000, 1, 1)
    for _ in range(100):
        date = start_date + datetime.timedelta(days=random.randint(0, 365 * 30))
        lat = random.uniform(-60, 60)
        lon = random.uniform(-180, 180)
        solar_noon = src.retrieval.utils.pressure_averaging.compute_solar_noon_time(
            lat, lon, date
        )
        assert solar_noon.date() == date


@pytest.mark.order(3)
@pytest.mark.quick
def test_pressure_averaging(download_sample_data: None) -> None:
    for filepath in [
        os.path.join(_DATALOGGER_DIR, "mc/datalogger-mc-20220602.csv"),
        os.path.join(_DATALOGGER_DIR, "so/datalogger-so-20170608.csv"),
        os.path.join(_DATALOGGER_DIR, "so/datalogger-so-20170609.csv"),
    ]:
        # the date is irrelevant, only the time is used
        pressure = src.retrieval.utils.pressure_averaging.compute_mean_pressure_around_noon(
            datetime.datetime(2022, 6, 1, 13, 0, 0, tzinfo=datetime.timezone.utc),
            filepath
        )
        assert isinstance(pressure, float)
        assert 900 <= pressure <= 1100
