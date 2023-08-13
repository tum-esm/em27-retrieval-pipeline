from typing import Literal
import pytest
from datetime import datetime
from src import custom_types, procedures
from src.custom_types import DownloadQuery, DownloadQueryLocation
from tests.fixtures import provide_container_config


@pytest.mark.ci
def test_get_query_list() -> None:
    l_0 = DownloadQueryLocation(lat=0, lon=0)
    l_1 = DownloadQueryLocation(lat=1, lon=1)
    l_2 = DownloadQueryLocation(lat=2, lon=2)
    l_3 = DownloadQueryLocation(lat=3, lon=3)
    l_4 = DownloadQueryLocation(lat=4, lon=4)

    daily_sensor_sets: dict[DownloadQueryLocation, dict[str, set[str]]] = {
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
        DownloadQuery(from_date="10000101", to_date="10000101", location=l_0),
        DownloadQuery(from_date="10000101", to_date="10000102", location=l_1),
        DownloadQuery(from_date="10000101", to_date="10000103", location=l_2),
        DownloadQuery(from_date="10000101", to_date="10000101", location=l_3),
        DownloadQuery(from_date="10000103", to_date="10000103", location=l_3),
        DownloadQuery(from_date="10000101", to_date="10000101", location=l_4),
        DownloadQuery(from_date="10000103", to_date="10000104", location=l_4),
        DownloadQuery(from_date="10000106", to_date="10000106", location=l_4),
    ]

    assert procedures.profiles.get_query_list(daily_sensor_sets) == expected_query_list


@pytest.mark.ci
def test_get_date_suffixes(provide_container_config: custom_types.Config) -> None:
    l = DownloadQueryLocation(lat=0, lon=0)

    def call(q: DownloadQuery, v: Literal["GGG2014", "GGG2020"]) -> list[str]:
        return procedures.profiles.get_date_suffixes(
            provide_container_config, q, v, utcnow=datetime(1000, 1, 10)
        )

    q = DownloadQuery(from_date="10000101", to_date="10000101", location=l)
    assert ["10000101_10000101"] == call(q, "GGG2014")

    q = DownloadQuery(from_date="10000101", to_date="10000103", location=l)
    assert ["10000101_10000103"] == call(q, "GGG2014")

    q = DownloadQuery(from_date="10000101", to_date="10000104", location=l)
    assert [
        "10000101_10000104",
        "10000101_10000103",
    ] == call(q, "GGG2014")

    q = DownloadQuery(from_date="10000103", to_date="10000104", location=l)
    assert [
        "10000103_10000104",
        "10000103_10000103",
    ] == call(q, "GGG2014")

    q = DownloadQuery(from_date="10000105", to_date="10000106", location=l)
    assert [
        "10000105_10000106",
        "10000105_10000105",
    ] == call(q, "GGG2014")

    q = DownloadQuery(from_date="10000101", to_date="10000101", location=l)
    assert ["10000101-10000102"] == call(q, "GGG2020")

    q = DownloadQuery(from_date="10000101", to_date="10000103", location=l)
    assert ["10000101-10000104"] == call(q, "GGG2020")

    q = DownloadQuery(from_date="10000101", to_date="10000104", location=l)
    assert [
        "10000101-10000105",
        "10000101-10000104",
    ] == call(q, "GGG2020")

    q = DownloadQuery(from_date="10000103", to_date="10000104", location=l)
    assert [
        "10000103-10000105",
        "10000103-10000104",
    ] == call(q, "GGG2020")

    q = DownloadQuery(from_date="10000105", to_date="10000106", location=l)
    assert [
        "10000105-10000107",
        "10000105-10000106",
    ] == call(q, "GGG2020")
