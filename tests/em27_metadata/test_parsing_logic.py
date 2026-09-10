import datetime
from src.em27_metadata.types import Setup, SetupsListItem


def test_equality() -> None:
    s1 = Setup(
        location_id="1",
        pressure_data_source="2",
        utc_offset=3,
        atmospheric_profile_location_id="4",
    )
    s2 = Setup(
        location_id="1",
        pressure_data_source="2",
        utc_offset=3,
        atmospheric_profile_location_id="4",
    )
    assert s1 == s2

    s2.atmospheric_profile_location_id = "5"
    assert s1 != s2

    s1.atmospheric_profile_location_id = "5"
    assert s1 == s2


def test_validation_alias() -> None:
    s1 = Setup(
        location_id="1",
        pressure_data_source="2",
        utc_offset=3,
        atmospheric_profile_location_id="4",
    )
    s2 = Setup(lid="1", pds="2", utc_offset=3, profile_lid="4")  # pyright: ignore[reportCallIssue]
    assert s1.location_id == s2.location_id
    assert s1.pressure_data_source == s2.pressure_data_source
    assert s1.utc_offset == s2.utc_offset
    assert s1.atmospheric_profile_location_id == s2.atmospheric_profile_location_id

    d = s2.model_dump()
    assert d["location_id"] == s2.location_id
    assert d["pressure_data_source"] == s2.pressure_data_source
    assert d["utc_offset"] == s2.utc_offset
    assert d["atmospheric_profile_location_id"] == s2.atmospheric_profile_location_id

    assert "lid" not in d
    assert "pds" not in d
    assert "profile_lid" not in d

    sli1 = SetupsListItem(
        from_datetime=datetime.datetime(2021, 1, 1),
        to_datetime=datetime.datetime(2021, 1, 2, 23, 59, 59),
        value=s1,
    )
    sli2 = SetupsListItem(
        from_dt=datetime.datetime(2021, 1, 1),  # pyright: ignore[reportCallIssue]
        to_dt=datetime.datetime(2021, 1, 2, 23, 59, 59),  # pyright: ignore[reportCallIssue]
        v=s2,  # pyright: ignore[reportCallIssue]
    )
    assert sli1 == sli2
