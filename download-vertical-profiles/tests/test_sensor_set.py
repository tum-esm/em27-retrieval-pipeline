import tum_esm_em27_metadata
from src import custom_types, procedures


def test_get_daily_sensor_sets() -> None:
    config = custom_types.Config(
        location_data=custom_types.LocationDataConfig(github_repository=""),
        request_scope=custom_types.RequestScopeConfig(
            dst_dir="/tmp", from_date="10000102", to_date="10000105"
        ),
        ftp_server=custom_types.FTPServerConfig(email="sosmsm"),
    )

    locations = [
        tum_esm_em27_metadata.types.Location(
            location_id="L1", details="...", lat=10.1, lon=10.1, alt=1
        ),
        tum_esm_em27_metadata.types.Location(
            location_id="L2", details="...", lat=9.9, lon=9.9, alt=1
        ),
        tum_esm_em27_metadata.types.Location(
            location_id="L3", details="...", lat=10.6, lon=10.6, alt=1
        ),
    ]
    sensors = [
        tum_esm_em27_metadata.types.Sensor(
            sensor_id="a",
            serial_number=1,
            utc_offsets=[],
            different_pressure_data_source=[],
            pressure_calibration_factors=[],
            locations=[
                tum_esm_em27_metadata.types.SensorLocation(
                    from_date="10000103", to_date="10000103", location_id="L1"
                ),
                tum_esm_em27_metadata.types.SensorLocation(
                    from_date="10000104", to_date="10000104", location_id="L3"
                ),
            ],
        ),
        tum_esm_em27_metadata.types.Sensor(
            sensor_id="b",
            serial_number=2,
            utc_offsets=[],
            different_pressure_data_source=[],
            pressure_calibration_factors=[],
            locations=[
                tum_esm_em27_metadata.types.SensorLocation(
                    from_date="10000103", to_date="10000104", location_id="L2"
                )
            ],
        ),
        tum_esm_em27_metadata.types.Sensor(
            sensor_id="c",
            serial_number=3,
            utc_offsets=[],
            different_pressure_data_source=[],
            pressure_calibration_factors=[],
            locations=[
                tum_esm_em27_metadata.types.SensorLocation(
                    from_date="10000101", to_date="10000106", location_id="L2"
                )
            ],
        ),
        tum_esm_em27_metadata.types.Sensor(
            sensor_id="d",
            serial_number=4,
            utc_offsets=[],
            different_pressure_data_source=[],
            pressure_calibration_factors=[],
            locations=[
                tum_esm_em27_metadata.types.SensorLocation(
                    from_date="10000102", to_date="10000105", location_id="L3"
                )
            ],
        ),
    ]

    expected_daily_sensor_sets = {
        custom_types.QueryLocation(lat=10, lon=10): {
            "10000102": {"c"},
            "10000103": {"a", "b", "c"},
            "10000104": {"b", "c"},
            "10000105": {"c"},
        },
        custom_types.QueryLocation(lat=11, lon=11): {
            "10000102": {"d"},
            "10000103": {"d"},
            "10000104": {"a", "d"},
            "10000105": {"d"},
        },
    }

    assert (
        procedures.get_daily_sensor_sets(
            config,
            em27_metadata=tum_esm_em27_metadata.interfaces.EM27MetadataInterface(
                locations, sensors, []
            ),
        )
        == expected_daily_sensor_sets
    )
