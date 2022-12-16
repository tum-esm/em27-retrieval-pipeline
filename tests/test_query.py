from typing import Any
from datetime import datetime
from unittest.mock import patch
from src.custom_types import QueryLocation, Query, Date, SensorId, FTPConfig, Version
from src.procedures.query import _get_date_suffixes, get_query_list


def test_get_query_list() -> None:

    l_0 = QueryLocation(lat=0, lon=0)
    l_1 = QueryLocation(lat=1, lon=1)
    l_2 = QueryLocation(lat=2, lon=2)
    l_3 = QueryLocation(lat=3, lon=3)
    l_4 = QueryLocation(lat=4, lon=4)

    daily_sensor_sets: dict[QueryLocation, dict[Date, set[SensorId]]] = {
        l_0: {
            "00010101": set(),
        },
        l_1: {
            "00010101": set(),
            "00010102": set(),
        },
        l_2: {
            "00010101": set(),
            "00010102": set(),
            "00010103": set(),
        },
        l_3: {
            "00010101": set(),
            "00010103": set(),
        },
        l_4: {
            "00010101": set(),
            "00010103": set(),
            "00010104": set(),
            "00010106": set(),
        },
    }

    query_list = [
        Query(from_date="00010101", to_date="00010101", location=l_0),
        Query(from_date="00010101", to_date="00010102", location=l_1),
        Query(from_date="00010101", to_date="00010103", location=l_2),
        Query(from_date="00010101", to_date="00010101", location=l_3),
        Query(from_date="00010103", to_date="00010103", location=l_3),
        Query(from_date="00010101", to_date="00010101", location=l_4),
        Query(from_date="00010103", to_date="00010104", location=l_4),
        Query(from_date="00010106", to_date="00010106", location=l_4),
    ]

    assert query_list == get_query_list(daily_sensor_sets)


@patch("src.procedures.query.datetime")
def test_get_date_suffixes(mock_dt: Any) -> None:

    mock_dt.utcnow.return_value = datetime(1, 1, 10)
    c = FTPConfig(email="_@_._", max_day_delay=7)
    l = QueryLocation(lat=0, lon=0)

    v: Version = "GGG2014"

    q = Query(from_date="00010101", to_date="00010101", location=l)
    assert ["00010101_00010101"] == _get_date_suffixes(c, q, v)
    q = Query(from_date="00010101", to_date="00010103", location=l)
    assert ["00010101_00010103"] == _get_date_suffixes(c, q, v)
    q = Query(from_date="00010101", to_date="00010104", location=l)
    assert ["00010101_00010104", "00010101_00010103"] == _get_date_suffixes(c, q, v)
    q = Query(from_date="00010103", to_date="00010104", location=l)
    assert ["00010103_00010104", "00010103_00010103"] == _get_date_suffixes(c, q, v)
    q = Query(from_date="00010105", to_date="00010106", location=l)
    assert ["00010105_00010106", "00010105_00010105"] == _get_date_suffixes(c, q, v)

    v = "GGG2020"

    q = Query(from_date="00010101", to_date="00010101", location=l)
    assert ["00010101-00010102"] == _get_date_suffixes(c, q, v)
    q = Query(from_date="00010101", to_date="00010103", location=l)
    assert ["00010101-00010104"] == _get_date_suffixes(c, q, v)
    q = Query(from_date="00010101", to_date="00010104", location=l)
    assert ["00010101-00010105", "00010101-00010104"] == _get_date_suffixes(c, q, v)
    q = Query(from_date="00010103", to_date="00010104", location=l)
    assert ["00010103-00010105", "00010103-00010104"] == _get_date_suffixes(c, q, v)
    q = Query(from_date="00010105", to_date="00010106", location=l)
    assert ["00010105-00010107", "00010105-00010106"] == _get_date_suffixes(c, q, v)
