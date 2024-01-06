import datetime
import em27_metadata
import pytest
import src
from src.profiles.generate_queries import ProfilesQueryLocation, list_requested_data
from ..fixtures import provide_config_template


@pytest.mark.order(3)
@pytest.mark.quick
def test_list_requested_data(provide_config_template: src.types.Config) -> None:
    metadata = em27_metadata.EM27MetadataInterface(
        locations=[
            em27_metadata.types.LocationMetadata(
                location_id="l1", details="l1 details", lat=1, lon=2, alt=0
            ),
            em27_metadata.types.LocationMetadata(
                location_id="l2", details="l2 details", lat=1, lon=3, alt=0
            ),
            em27_metadata.types.LocationMetadata(
                location_id="l3", details="l3 details", lat=2, lon=3, alt=0
            ),
        ],
        sensors=[
            em27_metadata.types.SensorMetadata(
                sensor_id="s1",
                serial_number=1,
                locations=[
                    em27_metadata.types.SensorTypes.Location(
                        from_datetime="2000-01-01T00:00:00+00:00",
                        to_datetime="2000-03-01T11:59:59+00:00",
                        location_id="l1",
                    ),
                    em27_metadata.types.SensorTypes.Location(
                        from_datetime="2000-03-01T12:00:00+00:00",
                        to_datetime="2000-05-01T23:59:59+00:00",
                        location_id="l3",
                    ),
                    em27_metadata.types.SensorTypes.Location(
                        from_datetime="2000-05-04T12:00:00+00:00",
                        to_datetime="2000-05-07T23:59:59+00:00",
                        location_id="l2",
                    ),
                ],
            ),
            em27_metadata.types.SensorMetadata(
                sensor_id="s2",
                serial_number=2,
                locations=[
                    em27_metadata.types.SensorTypes.Location(
                        from_datetime="2000-01-07T00:00:00+00:00",
                        to_datetime="2000-02-23T23:59:59+00:00",
                        location_id="l1",
                    ),
                    em27_metadata.types.SensorTypes.Location(
                        from_datetime="2000-05-05T12:00:00+00:00",
                        to_datetime="2000-05-08T23:59:59+00:00",
                        location_id="l2",
                    ),
                ],
            ),
        ],
        campaigns=[],
    )
    expected_data = {
        ProfilesQueryLocation(lat=1, lon=2):
            set(
                src.utils.functions.date_range(
                    datetime.date(2000, 1, 1),
                    datetime.date(2000, 3, 1),
                )
            ),
        ProfilesQueryLocation(lat=1, lon=3):
            set(
                src.utils.functions.date_range(
                    datetime.date(2000, 5, 4),
                    datetime.date(2000, 5, 8),
                )
            ),
        ProfilesQueryLocation(lat=2, lon=3):
            set(
                src.utils.functions.date_range(
                    datetime.date(2000, 3, 1),
                    datetime.date(2000, 5, 1),
                )
            ),
    }
    config = provide_config_template.model_copy(deep=True)
    assert config.profiles is not None
    config.profiles.scope.from_date = datetime.date(2000, 1, 1)
    config.profiles.scope.to_date = datetime.date(2000, 5, 8)

    actual_data = list_requested_data(config, metadata)
    assert actual_data.keys() == expected_data.keys()
    for k in actual_data.keys():
        assert actual_data[k] == expected_data[k]
