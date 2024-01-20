from typing import Generator
import datetime
import pytest
import src


@pytest.fixture
def keep_query_cache() -> Generator[None, None, None]:
    cache = src.profiles.cache.DownloadQueryCache.load()
    yield
    cache.dump()


@pytest.mark.order(3)
@pytest.mark.quick
def test_query_cache(keep_query_cache: None) -> None:
    cache = src.profiles.cache.DownloadQueryCache(root=[])
    cache.dump()

    cache = src.profiles.cache.DownloadQueryCache.load()
    assert len(cache.root) == 0

    # GGG2014
    assert len(cache.get_active_queries("GGG2014")) == 0
    for q in [
        src.types.DownloadQuery(
            lat=24,
            lon=30,
            from_date=datetime.date(2014, 1, 1),
            to_date=datetime.date(2014, 1, 6),
        ),
        src.types.DownloadQuery(
            lat=28,
            lon=30,
            from_date=datetime.date(2014, 1, 1),
            to_date=datetime.date(2014, 1, 2),
        ),
    ]:
        cache.add_query("GGG2014", q)
    assert len(cache.get_active_queries("GGG2014")) == 2

    # GGG2014
    assert len(cache.get_active_queries("GGG2020")) == 0
    for q in [
        src.types.DownloadQuery(
            lat=24,
            lon=30,
            from_date=datetime.date(2014, 1, 1),
            to_date=datetime.date(2014, 1, 6),
        ),
        src.types.DownloadQuery(
            lat=28,
            lon=30,
            from_date=datetime.date(2014, 1, 1),
            to_date=datetime.date(2014, 1, 2),
        ),
        src.types.DownloadQuery(
            lat=30,
            lon=30,
            from_date=datetime.date(2014, 4, 1),
            to_date=datetime.date(2014, 4, 5),
        )
    ]:
        cache.add_query("GGG2020", q)
    assert len(cache.get_active_queries("GGG2014")) == 2
    assert len(cache.get_active_queries("GGG2020")) == 3
