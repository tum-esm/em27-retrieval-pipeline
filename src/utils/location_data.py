import json
import os

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))

with open(f"{PROJECT_DIR}/em27-location-data/data/sensors.json") as f:
    _LOCATION_DATA_SENSORS: dict = json.load(f)
with open(f"{PROJECT_DIR}/em27-location-data/data/locations.json") as f:
    _LOCATION_DATA_LOCATIONS: dict = json.load(f)

class LocationData:

    @staticmethod
    def sensor_names() -> list[str]:
        return _LOCATION_DATA_SENSORS.keys()
    
    @staticmethod
    def get_serial_number(sensor_name: str) -> int:
        try:
            return _LOCATION_DATA_SENSORS[sensor_name]["serialNumber"]
        except KeyError:
            raise Exception(
                f'em27-location-data/data/sensors.json is invalid, "{sensor_name}"'
            )
    
    @staticmethod
    def get_location_list(sensor_name: str) -> int:
        try:
            return _LOCATION_DATA_SENSORS[sensor_name]["locations"]
        except KeyError:
            raise Exception(
                f'em27-location-data/data/sensors.json is invalid, "{sensor_name}"'
            )

    @staticmethod
    def get_coordinates(location: str):
        try:
            c = _LOCATION_DATA_LOCATIONS[location]
            return {k: c[k] for k in ["lat", "lon", "alt"]}
        except KeyError:
            raise Exception(
                f'em27-location-data/data/locations.json is invalid, "{location}" not found'
            )