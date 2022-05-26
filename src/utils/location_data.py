import json
import os

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))

with open(f"{PROJECT_DIR}/em27-location-data/data/sensors.json") as f:
    _LOCATION_DATA_SENSORS = json.load(f)
with open(f"{PROJECT_DIR}/em27-location-data/data/locations.json") as f:
    _LOCATION_DATA_LOCATIONS = json.load(f)


class LocationData:
    @staticmethod
    def get_location_for_sensor_date(sensor: str, date: int):
        _locations = _LOCATION_DATA_SENSORS[sensor]["locations"]
        if (date < _locations[0]["from"]) or (date > _locations[-1]["to"]):
            return None
        for _l in _locations:
            if (date >= _l["from"]) and (date <= _l["to"]):
                return _l["location"]
        raise Exception("em27-location-data/data/sensors.json is invalid")

    @staticmethod
    def get_coordinates_for_location(location: str):
        try:
            c = _LOCATION_DATA_LOCATIONS[location]
            return {k: c[k] for k in ["lat", "lon", "alt"]}
        except KeyError:
            raise Exception(
                f'em27-location-data/data/locations.json is invalid, "{location}" not found'
            )
