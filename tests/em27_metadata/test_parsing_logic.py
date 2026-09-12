from src.em27_metadata.types import Deployment, SensorMetadata, Setup, SetupsListItem


def test_equality() -> None:
    deployment_data = {
        "from_datetime": "2021-01-01T00:00:00Z",
        "to_datetime": "2021-01-02T23:59:59Z",
        "location_id": "1",
        "pressure_data_source": "2",
        "utc_offset": 3,
        "atmospheric_profile_location_id": "4",
    }
    d1 = Deployment(**deployment_data)  # pyright: ignore[reportArgumentType]
    d2 = Deployment(**deployment_data)  # pyright: ignore[reportArgumentType]
    assert d1 == d2

    d2.atmospheric_profile_location_id = "5"
    assert d1 != d2

    d1.atmospheric_profile_location_id = "5"
    assert d1 == d2


def test_validation_alias() -> None:
    d1 = Deployment(
        from_datetime="2021-01-01T00:00:00Z",
        to_datetime="2021-01-02T23:59:59Z",
        location_id="1",
        pressure_data_source="2",
        utc_offset=3,
        atmospheric_profile_location_id="4",
    )
    d2 = Deployment(
        from_dt="2021-01-01T00:00:00Z",  # pyright: ignore[reportCallIssue]
        to_dt="2021-01-02T23:59:59Z",  # pyright: ignore[reportCallIssue]
        lid="1",  # pyright: ignore[reportCallIssue]
        pds="2",  # pyright: ignore[reportCallIssue]
        utc_offset=3,
        profile_lid="4",  # pyright: ignore[reportCallIssue]
    )
    assert d1 == d2

    assert d2.model_dump() == {
        "from_datetime": "2021-01-01T00:00:00Z",
        "to_datetime": "2021-01-02T23:59:59Z",
        "location_id": "1",
        "pressure_data_source": "2",
        "utc_offset": 3,
        "atmospheric_profile_location_id": "4",
    }

