import datetime
import pytest
import tum_esm_utils
import src
from ..fixtures import provide_config_template  # pyright: ignore[reportUnusedImport]


@pytest.mark.order(3)
@pytest.mark.quick
def test_list_requested_data(provide_config_template: src.types.Config) -> None:
    metadata = src.em27_metadata.EM27MetadataInterface(
        locations=src.em27_metadata.types.LocationMetadataList(
            root=[
                src.em27_metadata.types.LocationMetadata(
                    location_id="l1", details="l1 details", lat=1, lon=2, alt_asl=0
                ),
                src.em27_metadata.types.LocationMetadata(
                    location_id="l2", details="l2 details", lat=1, lon=3, alt_asl=0
                ),
                src.em27_metadata.types.LocationMetadata(
                    location_id="l3", details="l3 details", lat=2, lon=3, alt_asl=0
                ),
            ]
        ),
        sensors=src.em27_metadata.types.SensorMetadataList(
            root=[
                src.em27_metadata.types.SensorMetadata(
                    sensor_id="s1",
                    serial_number=1,
                    setups=[
                        src.em27_metadata.types.SetupsListItem(
                            from_datetime="2000-01-01T00:00:00+0000",  # pyright: ignore[reportArgumentType]
                            to_datetime="2000-03-01T11:59:59+0000",  # pyright: ignore[reportArgumentType]
                            value=src.em27_metadata.types.Setup(location_id="l1"),
                        ),
                        src.em27_metadata.types.SetupsListItem(
                            from_datetime="2000-03-01T12:00:00+0000",  # pyright: ignore[reportArgumentType]
                            to_datetime="2000-05-01T23:59:59+0000",  # pyright: ignore[reportArgumentType]
                            value=src.em27_metadata.types.Setup(location_id="l3"),
                        ),
                        src.em27_metadata.types.SetupsListItem(
                            from_datetime="2000-05-04T12:00:00+0000",  # pyright: ignore[reportArgumentType]
                            to_datetime="2000-05-07T23:59:59+0000",  # pyright: ignore[reportArgumentType]
                            value=src.em27_metadata.types.Setup(location_id="l2"),
                        ),
                    ],
                ),
                src.em27_metadata.types.SensorMetadata(
                    sensor_id="s2",
                    serial_number=2,
                    setups=[
                        src.em27_metadata.types.SetupsListItem(
                            from_datetime="2000-01-07T00:00:00+0000",  # pyright: ignore[reportArgumentType]
                            to_datetime="2000-02-23T23:59:59+0000",  # pyright: ignore[reportArgumentType]
                            value=src.em27_metadata.types.Setup(location_id="l1"),
                        ),
                        src.em27_metadata.types.SetupsListItem(
                            from_datetime="2000-05-05T12:00:00+0000",  # pyright: ignore[reportArgumentType]
                            to_datetime="2000-05-08T23:59:59+0000",  # pyright: ignore[reportArgumentType]
                            value=src.em27_metadata.types.Setup(location_id="l2"),
                        ),
                    ],
                ),
            ]
        ),
        campaigns=src.em27_metadata.types.CampaignMetadataList(root=[]),
    )
    expected_data = {
        src.ggg_profiles_downloader.generate_queries.ProfilesQueryLocation(lat=1, lon=2): set(
            tum_esm_utils.timing.date_range(
                datetime.date(2000, 1, 1),
                datetime.date(2000, 3, 1),
            )
        ),
        src.ggg_profiles_downloader.generate_queries.ProfilesQueryLocation(lat=1, lon=3): set(
            tum_esm_utils.timing.date_range(
                datetime.date(2000, 5, 4),
                datetime.date(2000, 5, 8),
            )
        ),
        src.ggg_profiles_downloader.generate_queries.ProfilesQueryLocation(lat=2, lon=3): set(
            tum_esm_utils.timing.date_range(
                datetime.date(2000, 3, 1),
                datetime.date(2000, 5, 1),
            )
        ),
    }
    config = provide_config_template.model_copy(deep=True)
    assert config.ggg_profiles_downloader is not None
    assert config.ggg_profiles_downloader.scope is not None
    config.ggg_profiles_downloader.scope.from_date = "2000-01-01"
    config.ggg_profiles_downloader.scope.to_date = "2000-05-08"

    actual_data = src.ggg_profiles_downloader.generate_queries.list_desired_data(config, metadata)
    assert actual_data.keys() == expected_data.keys()
    for k in actual_data.keys():
        assert actual_data[k] == expected_data[k]
