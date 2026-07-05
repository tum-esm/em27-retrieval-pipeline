import datetime
import os
import random
import pytest
import tum_esm_utils
import src

_GROUND_PRESSURE_DIR = tum_esm_utils.files.rel_to_abs_path(
    "../../example/data/inputs/ground-pressure"
)


@pytest.mark.order(3)
@pytest.mark.quick
def test_solar_noon_computation() -> None:
    start_date = datetime.date(2000, 1, 1)
    rng = random.Random(0)
    for _ in range(100):
        date = start_date + datetime.timedelta(days=rng.randint(0, 365 * 30))
        lat = rng.uniform(-60, 60)
        lon = rng.uniform(-180, 180)
        solar_noon = src.retrieval.utils.pressure_averaging.compute_solar_noon_time(lat, lon, date)
        local_solar_noon = solar_noon + datetime.timedelta(hours=lon / 15)
        assert local_solar_noon.date() == date
        assert abs(
            local_solar_noon
            - datetime.datetime.combine(
                date,
                datetime.time(hour=12),
                tzinfo=datetime.timezone.utc,
            )
        ) < datetime.timedelta(minutes=20)


@pytest.mark.order(3)
@pytest.mark.quick
def test_pressure_averaging() -> None:
    for filepath in [
        os.path.join(_GROUND_PRESSURE_DIR, "mc/ground-pressure-mc-2022-06-02.csv"),
        os.path.join(_GROUND_PRESSURE_DIR, "so/ground-pressure-so-2017-06-08.csv"),
        os.path.join(_GROUND_PRESSURE_DIR, "so/ground-pressure-so-2017-06-09.csv"),
    ]:
        # the date is irrelevant, only the time is used
        pressure = src.retrieval.utils.pressure_averaging.compute_mean_pressure_around_noon(
            datetime.datetime(2022, 6, 1, 13, 0, 0, tzinfo=datetime.timezone.utc), filepath
        )
        assert isinstance(pressure, float)
        assert 900 <= pressure <= 1100
