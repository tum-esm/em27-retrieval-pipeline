from datetime import datetime
import json
import os

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
CLOUD_DATA_ROOT = "/mnt/measurementData/mu"
IGNORE_DATES_BEFORE = 20220101

with open(f"{PROJECT_DIR}/em27-location-data/data/sensors.json") as f:
    LOCATION_DATA_SENSORS = json.load(f)
with open(f"{PROJECT_DIR}/em27-location-data/data/locations.json") as f:
    LOCATION_DATA_LOCATIONS = json.load(f)


def _date_string_is_valid(date_string: str):
    try:
        datetime.strptime(date_string, "%Y%m%d")
        return int(date_string) >= IGNORE_DATES_BEFORE
    except (ValueError, TypeError):
        return False


def _get_location_for_sensor_date(sensor: str, date: int):
    _locations = LOCATION_DATA_SENSORS[sensor]["locations"]
    if (date < _locations[0]["from"]) or (date > _locations[-1]["to"]):
        return None
    for _l in _locations:
        if (date >= _l["from"]) and (date <= _l["to"]):
            return _l["location"]
    raise Exception("em27-location-data/data/sensors.json is invalid")


class RetrievalSessionQueue:
    def __init__(self, sensor_names: list[str]):

        self.sensor_names = sensor_names
        self.data_directories = self._list_data_directories()
        self.retrieval_sessions = self._generate_retrieval_sessions()

    def __iter__(self):
        for s in self.retrieval_sessions:
            yield s

    def _list_data_directories(self):
        data_directories = {}
        for s in self.sensor_names:
            ds = [
                x
                for x in os.listdir(f"{CLOUD_DATA_ROOT}/{s}_ifg")
                if len(x) >= 8 and _date_string_is_valid(x[:8])
            ]
            for d in ds:
                if len(d) > 8:
                    os.rename(
                        f"{CLOUD_DATA_ROOT}/{s}_ifg/{d}",
                        f"{CLOUD_DATA_ROOT}/{s}_ifg/{d[:8]}",
                    )
            data_directories[s] = list(sorted([int(d[:8]) for d in ds]))
        return data_directories

    def _generate_retrieval_sessions(self):
        retrieval_sessions = []
        for sensor, sensor_dates in self.data_directories.items():
            for sensor_date in sensor_dates:
                location = _get_location_for_sensor_date(sensor, sensor_date)
                if location is None:
                    print(f"no location found for {sensor}/{sensor_date}")
                    continue

                if (
                    (len(retrieval_sessions) == 0)
                    or (retrieval_sessions[-1]["sensor"] != sensor)
                    or (retrieval_sessions[-1]["location"] != location)
                ):
                    try:
                        coordinates_dict = LOCATION_DATA_LOCATIONS[location]
                    except KeyError:
                        raise Exception(
                            f'em27-location-data/data/locations.json is invalid, "{location}" not found'
                        )
                    retrieval_sessions.append(
                        {
                            "sensor": sensor,
                            "location": location,
                            "dates": [],
                            **coordinates_dict,
                        }
                    )
                retrieval_sessions[-1]["dates"].append(sensor_date)
        return retrieval_sessions


if __name__ == "__main__":
    queue = RetrievalSessionQueue(sensor_names=["ma", "mb", "mc", "md", "me"])

    for session in queue:
        print(session["sensor"], session["location"], len(session["dates"]))
