from typing import Any, Literal
from datetime import datetime
from unittest.mock import patch
from src import custom_types, procedures
from src.custom_types import Query, QueryLocation


def test_get_query_list() -> None:
    l_0 = QueryLocation(lat=0, lon=0)
    l_1 = QueryLocation(lat=1, lon=1)
    l_2 = QueryLocation(lat=2, lon=2)
    l_3 = QueryLocation(lat=3, lon=3)
    l_4 = QueryLocation(lat=4, lon=4)

    daily_sensor_sets: dict[QueryLocation, dict[str, set[str]]] = {
        l_0: {
            "10000101": set(),
        },
        l_1: {
            "10000101": set(),
            "10000102": set(),
        },
        l_2: {
            "10000101": set(),
            "10000102": set(),
            "10000103": set(),
        },
        l_3: {
            "10000101": set(),
            "10000103": set(),
        },
        l_4: {
            "10000101": set(),
            "10000103": set(),
            "10000104": set(),
            "10000106": set(),
        },
    }

    expected_query_list = [
        Query(from_date="10000101", to_date="10000101", location=l_0),
        Query(from_date="10000101", to_date="10000102", location=l_1),
        Query(from_date="10000101", to_date="10000103", location=l_2),
        Query(from_date="10000101", to_date="10000101", location=l_3),
        Query(from_date="10000103", to_date="10000103", location=l_3),
        Query(from_date="10000101", to_date="10000101", location=l_4),
        Query(from_date="10000103", to_date="10000104", location=l_4),
        Query(from_date="10000106", to_date="10000106", location=l_4),
    ]

    assert procedures.get_query_list(daily_sensor_sets) == expected_query_list


@patch("src.procedures.query.datetime")
def test_get_date_suffixes(mock_dt: Any) -> None:

    mock_dt.utcnow.return_value = datetime(1000, 1, 10)
    c = custom_types.Config(
        location_data=custom_types.LocationDataConfig(github_repository=""),
        request_scope=custom_types.RequestScopeConfig(dst_dir="/tmp"),
        ftp_server=custom_types.FTPServerConfig(email="_@_._", max_day_delay=7),
    )
    l = QueryLocation(lat=0, lon=0)

    v: Literal["GGG2014", "GGG2020"] = "GGG2014"

    q = Query(from_date="10000101", to_date="10000101", location=l)
    assert ["10000101_10000101"] == procedures.get_date_suffixes(c, q, v)

    q = Query(from_date="10000101", to_date="10000103", location=l)
    assert ["10000101_10000103"] == procedures.get_date_suffixes(c, q, v)

    q = Query(from_date="10000101", to_date="10000104", location=l)
    assert ["10000101_10000104", "10000101_10000103"] == procedures.get_date_suffixes(
        c, q, v
    )

    q = Query(from_date="10000103", to_date="10000104", location=l)
    assert ["10000103_10000104", "10000103_10000103"] == procedures.get_date_suffixes(
        c, q, v
    )

    q = Query(from_date="10000105", to_date="10000106", location=l)
    assert ["10000105_10000106", "10000105_10000105"] == procedures.get_date_suffixes(
        c, q, v
    )

    v = "GGG2020"

    q = Query(from_date="10000101", to_date="10000101", location=l)
    assert ["10000101-10000102"] == procedures.get_date_suffixes(c, q, v)

    q = Query(from_date="10000101", to_date="10000103", location=l)
    assert ["10000101-10000104"] == procedures.get_date_suffixes(c, q, v)

    q = Query(from_date="10000101", to_date="10000104", location=l)
    assert ["10000101-10000105", "10000101-10000104"] == procedures.get_date_suffixes(
        c, q, v
    )

    q = Query(from_date="10000103", to_date="10000104", location=l)
    assert ["10000103-10000105", "10000103-10000104"] == procedures.get_date_suffixes(
        c, q, v
    )

    q = Query(from_date="10000105", to_date="10000106", location=l)
    assert ["10000105-10000107", "10000105-10000106"] == procedures.get_date_suffixes(
        c, q, v
    )
