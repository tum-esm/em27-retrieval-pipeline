import datetime
import random
import pytest
import src


@pytest.mark.order(3)
@pytest.mark.quick
def test_solar_noon_computation() -> None:
    start_date = datetime.date(2000, 1, 1)
    for _ in range(100):
        date = start_date + datetime.timedelta(days=random.randint(0, 365 * 30))
        lat = random.uniform(-90, 90)
        lon = random.uniform(-180, 180)
        solar_noon = src.utils.functions.compute_solar_noon_time(lat, lon, date)
        assert solar_noon.date() == date
