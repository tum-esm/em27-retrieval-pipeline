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


def test_legacy_deployment_class_names_and_value_shape_are_supported() -> None:
    deployment = SetupsListItem.model_validate(
        {
            "from_dt": "2021-01-01T00:00:00Z",
            "to_dt": "2021-01-02T23:59:59Z",
            "value": {
                "location_id": "1",
                "pressure_data_source": "2",
                "utc_offset": 3,
                "atmospheric_profile_location_id": "4",
            },
        }
    )

    assert Setup is Deployment
    assert SetupsListItem is Deployment
    assert deployment.location_id == "1"
    assert deployment.value.location_id == "1"
    assert "value" not in deployment.model_dump()


def test_sensor_metadata_deployments_are_backwards_compatible() -> None:
    flat_deployment = {
        "from_datetime": "2021-01-01T00:00:00Z",
        "to_datetime": "2021-01-02T23:59:59Z",
        "location_id": "flat-location",
    }
    legacy_deployment = {
        "from_datetime": "2021-01-01T00:00:00Z",
        "to_datetime": "2021-01-02T23:59:59Z",
        "value": {"location_id": "legacy-location"},
    }

    canonical_metadata = SensorMetadata.model_validate(
        {
            "sensor_id": "canonical-sensor",
            "serial_number": 1,
            "deployments": [flat_deployment],
        }
    )
    legacy_metadata = SensorMetadata.model_validate(
        {
            "sensor_id": "legacy-sensor",
            "serial_number": 2,
            "setups": [legacy_deployment],
        }
    )

    for metadata, expected_location_id in (
        (canonical_metadata, "flat-location"),
        (legacy_metadata, "legacy-location"),
    ):
        assert metadata.deployments[0].location_id == expected_location_id
        assert metadata.setups[0].location_id == expected_location_id
        assert metadata.deployments[0].value.location_id == expected_location_id
        assert metadata.setups[0].value.location_id == expected_location_id
        assert metadata.setups is metadata.deployments

        dumped_metadata = metadata.model_dump()
        assert "deployments" in dumped_metadata
        assert "setups" not in dumped_metadata
