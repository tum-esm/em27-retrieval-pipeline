import json
import os
from typing import Optional
from src import types

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))


class LocationData:
    def __init__(self, config: types.ConfigDict) -> None:
        types.validate_location_data(config)

        with open(f"{PROJECT_DIR}/location-data/data/sensors.json") as f:
            self.sensor_locations: dict[str, types.SensorLocationDict] = json.load(f)
        with open(f"{PROJECT_DIR}/location-data/data/locations.json") as f:
            self.location_coordinates: dict[
                str, types.LocationCoordinatesDict
            ] = json.load(f)

    def get_serial_number_for_sensor(self, sensor: str) -> int:
        return self.sensors[sensor]["serial_number"]

    def get_coordinates_for_location(
        self, location: str
    ) -> types.LocationCoordinatesDict:
        return self.location_coordinates[location]

    def get_location_for_date(self, sensor: str, date: str) -> Optional[str]:
        matching_time_frames = list(
            filter(
                lambda t: t["from_date"] <= int(date) and t["to_date"] >= int(date),
                self.sensors[sensor]["locations"],
            )
        )
        if len(matching_time_frames) == 0:
            return None

        assert len(matching_time_frames) == 1, (
            "multiple matching time frames found for "
            + f"{sensor}/{date}: {matching_time_frames}"
        )

        return matching_time_frames[0]
