import tum_esm_em27_metadata
from src import custom_types, procedures
from tests.fixtures import provide_container_config


def test_get_daily_sensor_sets(provide_container_config: custom_types.Config) -> None:
    config = provide_container_config
    config.vertical_profiles.request_scope.from_date = "10000102"
    config.vertical_profiles.request_scope.to_date = "10000105"

    locations = [
        tum_esm_em27_metadata.types.LocationMetadata(
            location_id="L1", details="...", lat=10.1, lon=10.1, alt=1
        ),
        tum_esm_em27_metadata.types.LocationMetadata(
            location_id="L2", details="...", lat=9.9, lon=9.9, alt=1
        ),
        tum_esm_em27_metadata.types.LocationMetadata(
            location_id="L3", details="...", lat=10.6, lon=10.6, alt=1
        ),
    ]
    sensors = [
        tum_esm_em27_metadata.types.SensorMetadata(
            sensor_id="a",
            serial_number=1,
            different_utc_offsets=[],
            different_pressure_data_sources=[],
            different_pressure_calibration_factors=[],
            different_output_calibration_factors=[],
            locations=[
                tum_esm_em27_metadata.types.SensorTypes.Location(
                    from_date="10000103", to_date="10000103", location_id="L1"
                ),
                tum_esm_em27_metadata.types.SensorTypes.Location(
                    from_date="10000104", to_date="10000104", location_id="L3"
                ),
            ],
        ),
        tum_esm_em27_metadata.types.SensorMetadata(
            sensor_id="b",
            serial_number=2,
            different_utc_offsets=[],
            different_pressure_data_sources=[],
            different_pressure_calibration_factors=[],
            different_output_calibration_factors=[],
            locations=[
                tum_esm_em27_metadata.types.SensorTypes.Location(
                    from_date="10000103", to_date="10000104", location_id="L2"
                )
            ],
        ),
        tum_esm_em27_metadata.types.SensorMetadata(
            sensor_id="c",
            serial_number=3,
            different_utc_offsets=[],
            different_pressure_data_sources=[],
            different_pressure_calibration_factors=[],
            different_output_calibration_factors=[],
            locations=[
                tum_esm_em27_metadata.types.SensorTypes.Location(
                    from_date="10000101", to_date="10000106", location_id="L2"
                )
            ],
        ),
        tum_esm_em27_metadata.types.SensorMetadata(
            sensor_id="d",
            serial_number=4,
            different_utc_offsets=[],
            different_pressure_data_sources=[],
            different_pressure_calibration_factors=[],
            different_output_calibration_factors=[],
            locations=[
                tum_esm_em27_metadata.types.SensorTypes.Location(
                    from_date="10000102", to_date="10000105", location_id="L3"
                )
            ],
        ),
    ]

    expected_daily_sensor_sets = {
        custom_types.DownloadQueryLocation(lat=10, lon=10): {
            "10000102": {"c"},
            "10000103": {"a", "b", "c"},
            "10000104": {"b", "c"},
            "10000105": {"c"},
        },
        custom_types.DownloadQueryLocation(lat=11, lon=11): {
            "10000102": {"d"},
            "10000103": {"d"},
            "10000104": {"a", "d"},
            "10000105": {"d"},
        },
    }

    assert (
        procedures.profiles.get_daily_sensor_sets(
            config,
            em27_metadata=tum_esm_em27_metadata.interfaces.EM27MetadataInterface(
                locations, sensors, []
            ),
        )
        == expected_daily_sensor_sets
    )
