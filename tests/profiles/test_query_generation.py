import random
import datetime
import pytest
import tum_esm_utils
import src
from .utils import generate_random_locations, generate_random_dates


@pytest.mark.order(3)
@pytest.mark.quick
def test_compute_missing_data() -> None:
    random_locations = generate_random_locations(30)
    random_dates = generate_random_dates(2000)
    for _ in range(20):
        downloaded_data = {
            l: set(random.sample(random_dates, 300))
            for l in random.sample(random_locations, 15)
        }
        requested_data = {
            l: set(random.sample(random_dates, 300))
            for l in random.sample(random_locations, 15)
        }
        missing_data = src.profiles.generate_queries.compute_missing_data(
            requested_data, downloaded_data
        )
        for l in requested_data.keys():
            rq = requested_data[l] if l in requested_data else set()
            dl = downloaded_data[l] if l in downloaded_data else set()
            ms = missing_data[l] if l in missing_data else set()
            if l not in missing_data.keys():
                assert rq.issubset(dl)
            else:
                assert ms.issubset(rq)
                assert ms.isdisjoint(dl)
                assert ms.union(dl).issuperset(rq)


@pytest.mark.order(3)
def test_time_period_generation() -> None:
    for _ in range(20):
        from_date = datetime.date(
            random.randint(2000, 2023),
            random.randint(1, 12),
            random.randint(1, 28),
        )
        to_date = from_date + datetime.timedelta(days=random.randint(100, 365))
        required_dates = set(
            random.sample(
                tum_esm_utils.timing.date_range(from_date, to_date), random.randint(10, 100)
            )
        )
        time_periods = sorted(
            src.profiles.generate_queries.compute_time_periods(required_dates),
            key=lambda tp: tp.from_date
        )
        for tp1, tp2 in zip(time_periods[:-1], time_periods[1 :]):
            assert tp1.to_date < tp2.from_date
        requested_dates: set[datetime.date] = set()
        for tp in time_periods:
            assert 0 <= (tp.to_date - tp.from_date).days <= 6
            requested_dates.update(tum_esm_utils.timing.date_range(tp.from_date, tp.to_date))
        assert requested_dates.issuperset(required_dates)
