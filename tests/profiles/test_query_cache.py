import datetime
from typing import Generator
import pytest
from src import types
from src.profiles.cache import DownloadQueryCache


@pytest.fixture
def keep_query_cache() -> Generator[None, None, None]:
    cache = DownloadQueryCache.load()
    yield
    cache.dump()


def test_query_cache(keep_query_cache: None) -> None:
    cache = DownloadQueryCache(root=[])
    cache.dump()

    cache = DownloadQueryCache.load()
    assert len(cache.root) == 0

    # GGG2014
    assert len(cache.get_active_queries("GGG2014")) == 0
    cache.add_queries(
        "GGG2014",
        [
            types.DownloadQuery(
                lat=24,
                lon=30,
                from_date=datetime.date(2014, 1, 1),
                to_date=datetime.date(2014, 1, 6),
            ),
            types.DownloadQuery(
                lat=28,
                lon=30,
                from_date=datetime.date(2014, 1, 1),
                to_date=datetime.date(2014, 1, 2),
            )
        ],
    )
    assert len(cache.get_active_queries("GGG2014")) == 2

    # GGG2014
    assert len(cache.get_active_queries("GGG2020")) == 0
    cache.add_queries(
        "GGG2020",
        [
            types.DownloadQuery(
                lat=24,
                lon=30,
                from_date=datetime.date(2014, 1, 1),
                to_date=datetime.date(2014, 1, 6),
            ),
            types.DownloadQuery(
                lat=28,
                lon=30,
                from_date=datetime.date(2014, 1, 1),
                to_date=datetime.date(2014, 1, 2),
            ),
            types.DownloadQuery(
                lat=30,
                lon=30,
                from_date=datetime.date(2014, 4, 1),
                to_date=datetime.date(2014, 4, 5),
            )
        ],
    )
    assert len(cache.get_active_queries("GGG2014")) == 2
    assert len(cache.get_active_queries("GGG2020")) == 3
