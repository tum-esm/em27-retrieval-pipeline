import json
import os

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))


def check_for_location_data(f):
    def wrapped_f(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except (FileNotFoundError, KeyError):
            raise Exception("Please run fetch-location-data.py first")

    return wrapped_f


class LocationData:
    @check_for_location_data
    def __init__(self):
        with open(f"{PROJECT_DIR}/location-data/data/sensors.json") as f:
            self.sensors: dict = json.load(f)
        with open(f"{PROJECT_DIR}/location-data/data/locations.json") as f:
            self.locations: dict = json.load(f)

    def sensor_names(self) -> list[str]:
        return self.sensors.keys()

    @check_for_location_data
    def get_serial_number(self, sensor_name: str) -> int:
        return self.sensors[sensor_name]["serialNumber"]

    @check_for_location_data
    def get_location_list(self, sensor_name: str) -> int:
        return self.sensors[sensor_name]["locations"]

    @check_for_location_data
    def get_location_for_date(self, sensor_name: str, date: int):
        _locations = self.sensors[sensor_name]["locations"]
        if (date < _locations[0]["from"]) or (date > _locations[-1]["to"]):
            return None
        for _l in _locations:
            if (date >= _l["from"]) and (date <= _l["to"]):
                return _l["location"]
        raise FileNotFoundError()

    @check_for_location_data
    def get_coordinates(self, location: str):
        c = self.locations[location]
        return {k: c[k] for k in ["lat", "lon", "alt"]}
