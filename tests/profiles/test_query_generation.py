import os
import random
import datetime
import tempfile
from typing import Any
import src
from src.profiles.generate_queries import (
    list_downloaded_data,
    list_requested_data,
    compute_missing_data,
    compute_time_periods,
    ProfilesQueryLocation,
)
from ..fixtures import provide_config_template

TEST_LOCATIONS = [
    ProfilesQueryLocation(lat=lat, lon=lon) for lat in range(-90, 90, 5)
    for lon in range(-180, 180, 5)
]
TEST_DATES = src.utils.functions.date_range(
    datetime.date(2018, 1, 1),
    datetime.date(2023, 12, 31),
)


def generate_random_locations(n: int) -> list[ProfilesQueryLocation]:
    assert n <= len(TEST_LOCATIONS)
    return random.sample(TEST_LOCATIONS, n)


def generate_random_dates(n: int) -> list[datetime.date]:
    assert n <= len(TEST_DATES)
    return random.sample(TEST_DATES, n)


def test_list_downloaded_data(
    provide_config_template: src.types.Config
) -> None:
    random_locations = generate_random_locations(n=30)
    random_dates = generate_random_dates(n=2000)
    cs = {
        l: src.utils.text.get_coordinates_slug(l.lat, l.lon)
        for l in random_locations
    }
    config = provide_config_template.model_copy(deep=True)
    assert config.profiles is not None
    config.profiles.scope.from_date = min(random_dates)
    config.profiles.scope.to_date = max(random_dates)
    for _ in range(5):
        downloaded_data = {
            l: set(random.sample(random_dates, 30))
            for l in random.sample(random_locations, 5)
        }
        model_filenames: dict[Any, list[str]] = {
            "GGG2014": [
                f"{d.strftime('%Y%m%d')}_{cs[l]}.{e}" for e in ["map", "mod"]
                for l in downloaded_data.keys() for d in downloaded_data[l]
            ],
            "GGG2020": [
                f"{d.strftime('%Y%m%d')}{h:02d}_{cs[l]}.{e}"
                for e in ["map", "mod", "vmr"] for l in downloaded_data.keys()
                for d in downloaded_data[l] for h in range(0, 24, 3)
            ],
        }
        for model, filenames in model_filenames.items():
            with tempfile.TemporaryDirectory() as tmpdir:
                config.general.data.atmospheric_profiles.root = tmpdir
                os.mkdir(os.path.join(tmpdir, model))
                for filename in filenames:
                    with open(os.path.join(tmpdir, model, filename), "w"):
                        pass
                downloaded = list_downloaded_data(config, model)
                assert downloaded.keys() == downloaded_data.keys()
                for l in downloaded_data.keys():
                    assert downloaded[l] == downloaded_data[l]


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
        missing_data = compute_missing_data(requested_data, downloaded_data)
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
                src.utils.functions.date_range(from_date, to_date),
                random.randint(10, 100)
            )
        )
        time_periods = sorted(
            compute_time_periods(required_dates), key=lambda tp: tp.from_date
        )
        for tp1, tp2 in zip(time_periods[:-1], time_periods[1 :]):
            assert tp1.to_date < tp2.from_date
        requested_dates: set[datetime.date] = set()
        for tp in time_periods:
            assert 0 <= (tp.to_date - tp.from_date).days <= 6
            requested_dates.update(
                src.utils.functions.date_range(tp.from_date, tp.to_date)
            )
        assert requested_dates.issuperset(required_dates)
