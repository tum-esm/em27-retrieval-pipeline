import datetime
import random
import tum_esm_utils
import src

TEST_LOCATIONS = [
    src.profiles.generate_queries.ProfilesQueryLocation(lat=lat, lon=lon)
    for lat in range(-90, 90, 5) for lon in range(-180, 180, 5)
]
TEST_DATES = tum_esm_utils.timing.date_range(
    datetime.date(2018, 1, 1),
    datetime.date(2023, 12, 31),
)


def generate_random_locations(n: int) -> list[src.profiles.generate_queries.ProfilesQueryLocation]:
    assert n <= len(TEST_LOCATIONS)
    return random.sample(TEST_LOCATIONS, n)


def generate_random_dates(n: int) -> list[datetime.date]:
    assert n <= len(TEST_DATES)
    return random.sample(TEST_DATES, n)
