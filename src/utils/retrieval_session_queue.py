from datetime import datetime
import os
import sys

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
sys.path.append(PROJECT_DIR)

from src.utils.location_data import LocationData

CLOUD_DATA_ROOT = "/mnt/measurementData/mu"
IGNORE_DATES_BEFORE = 20220101


def _date_string_is_valid(date_string: str):
    try:
        datetime.strptime(date_string, "%Y%m%d")
        return int(date_string) >= IGNORE_DATES_BEFORE
    except (ValueError, TypeError):
        return False


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
                location = LocationData.get_location(sensor, sensor_date)
                if location is None:
                    print(f"no location found for {sensor}/{sensor_date}")
                    continue

                if (
                    (len(retrieval_sessions) == 0)
                    or (retrieval_sessions[-1]["sensor"] != sensor)
                    or (retrieval_sessions[-1]["location"] != location)
                ):
                    retrieval_sessions.append(
                        {
                            "sensor": sensor,
                            "location": location,
                            "dates": [],
                            **LocationData.get_coordinates(location),
                            "serial_number": LocationData.get_serial_number(sensor),
                        }
                    )
                retrieval_sessions[-1]["dates"].append(sensor_date)
        return retrieval_sessions


if __name__ == "__main__":
    queue = RetrievalSessionQueue(sensor_names=["ma", "mb", "mc", "md", "me"])

    for session in queue:
        print(
            str(len(session["dates"])).zfill(3),
            session["dates"][0],
            session["dates"][-1],
            session["sensor"],
            session["location"],
        )
