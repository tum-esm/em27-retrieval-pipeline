import json
from src.utils import load_setup

PROJECT_DIR, CONFIG = load_setup(validate=False)

class LocationData:

    def __init__(self):
        try:
            with open(f"{PROJECT_DIR}/location-data/data/sensors.json") as f:
                self.sensors: dict = json.load(f)
            with open(f"{PROJECT_DIR}/location-data/data/locations.json") as f:
                self.locations: dict = json.load(f)
        except FileNotFoundError:
            raise Exception("Please run fetch-location-data.py first")

    def sensor_names(self) -> list[str]:
        return self.sensors.keys()
    
    def get_serial_number(self, sensor_name: str) -> int:
        try:
            return self.sensors[sensor_name]["serialNumber"]
        except KeyError:
            raise Exception(
                f'em27-location-data/data/sensors.json is invalid, "{sensor_name}"'
            )
    
    def get_location_list(self, sensor_name: str) -> int:
        try:
            return self.sensors[sensor_name]["locations"]
        except KeyError:
            raise Exception(
                f'em27-location-data/data/sensors.json is invalid, "{sensor_name}"'
            )

    def get_coordinates(self, location: str):
        try:
            c = self.locations[location]
            return {k: c[k] for k in ["lat", "lon", "alt"]}
        except KeyError:
            raise Exception(
                f'em27-location-data/data/locations.json is invalid, "{location}" not found'
            )