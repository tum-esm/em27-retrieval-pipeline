from src.procedures.sensor_set import get_daily_sensor_sets

from src.custom_types import (
    RequestConfig,
    Location,
    Sensor,
    QueryLocation,
    SensorLocation,
)


def test_get_daily_sensor_sets() -> None:

    config = RequestConfig(from_date="10000102", to_date="10000105")
    locations = {
        "L1": Location(details="", lat=10.1, lon=10.1, alt=1),
        "L2": Location(details="", lat=9.9, lon=9.9, alt=1),
        "L3": Location(details="", lat=10.6, lon=10.6, alt=1),
    }
    sensors = {
        "A": Sensor(
            serial_number=0,
            utc_offsets=[],
            locations=[
                SensorLocation(from_date="10000103", to_date="10000103", location="L1"),
                SensorLocation(from_date="10000104", to_date="10000104", location="L3"),
            ],
        ),
        "B": Sensor(
            serial_number=0,
            utc_offsets=[],
            locations=[SensorLocation(from_date="10000103", to_date="10000104", location="L2")],
        ),
        "C": Sensor(
            serial_number=0,
            utc_offsets=[],
            locations=[SensorLocation(from_date="10000101", to_date="10000106", location="L2")],
        ),
        "D": Sensor(
            serial_number=0,
            utc_offsets=[],
            locations=[SensorLocation(from_date="10000102", to_date="10000105", location="L3")],
        ),
    }

    daily_sensor_sets = {
        QueryLocation(lat=10, lon=10): {
            "10000102": {"C"},
            "10000103": {"A", "B", "C"},
            "10000104": {"B", "C"},
            "10000105": {"C"},
        },
        QueryLocation(lat=11, lon=11): {
            "10000102": {"D"},
            "10000103": {"D"},
            "10000104": {"A", "D"},
            "10000105": {"D"},
        },
    }

    assert daily_sensor_sets == get_daily_sensor_sets(config, locations, sensors)
