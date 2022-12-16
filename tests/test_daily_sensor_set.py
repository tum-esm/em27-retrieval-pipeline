from src.procedures.sensor_set import get_daily_sensor_sets

from src.custom_types import (
    RequestConfig,
    Location,
    Sensor,
    QueryLocation,
    SensorLocation,
)


def test_get_daily_sensor_sets() -> None:

    config = RequestConfig(from_date="00010102", to_date="00010105")
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
                SensorLocation(from_date="00010103", to_date="00010103", location="L1"),
                SensorLocation(from_date="00010104", to_date="00010104", location="L3"),
            ],
        ),
        "B": Sensor(
            serial_number=0,
            utc_offsets=[],
            locations=[SensorLocation(from_date="00010103", to_date="00010104", location="L2")],
        ),
        "C": Sensor(
            serial_number=0,
            utc_offsets=[],
            locations=[SensorLocation(from_date="00010101", to_date="00010106", location="L2")],
        ),
        "D": Sensor(
            serial_number=0,
            utc_offsets=[],
            locations=[SensorLocation(from_date="00010102", to_date="00010105", location="L3")],
        ),
    }

    daily_sensor_sets = {
        QueryLocation(lat=10, lon=10): {
            "00010102": {"C"},
            "00010103": {"A", "B", "C"},
            "00010104": {"B", "C"},
            "00010105": {"C"},
        },
        QueryLocation(lat=11, lon=11): {
            "00010102": {"D"},
            "00010103": {"D"},
            "00010104": {"A", "D"},
            "00010105": {"D"},
        },
    }

    assert daily_sensor_sets == get_daily_sensor_sets(config, locations, sensors)
