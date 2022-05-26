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


class RetrievalQueue:
    def __init__(self, sensor_names: list[str]):

        self.sensor_names = sensor_names
        self.data_directories = self._list_data_directories()
        self.queue = self._generate_queue()

    def __iter__(self):
        for s in self.queue:
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

    def _generate_queue(self):
        queue = []
        for sensor, sensor_dates in self.data_directories.items():
            for sensor_date in sensor_dates:
                location = LocationData.get_location(sensor, sensor_date)
                if location is None:
                    print(f"no location found for {sensor}/{sensor_date}")
                    continue

                queue.append(
                    {
                        "sensor": sensor,
                        "location": location,
                        "date": sensor_date,
                        **LocationData.get_coordinates(location),
                        "serial_number": LocationData.get_serial_number(sensor),
                    }
                )
        return queue


if __name__ == "__main__":
    queue = RetrievalQueue(sensor_names=["ma", "mb", "mc", "md", "me"])

    for session in list(queue)[:4]:
        print(session)

    """
    The retrieval queue looks like this:
    [
        {
            'sensor': 'mb', 'location': 'FEL', 'date': 20220512, 
            'lat': 48.148, 'lon': 11.73, 'alt': 536, 'serial_number': 86
        }, {
            'sensor': 'mb', 'location': 'FEL', 'date': 20220513,
            'lat': 48.148, 'lon': 11.73, 'alt': 536, 'serial_number': 86
        }, {
            'sensor': 'mb', 'location': 'TUM_I', 'date': 20220514,
            'lat': 48.151, 'lon': 11.569, 'alt': 539, 'serial_number': 86
        }, {
            'sensor': 'mb', 'location': 'TUM_I', 'date': 20220515, 
            'lat': 48.151, 'lon': 11.569, 'alt': 539, 'serial_number': 86
        }, {
            'sensor': 'mc', 'location': 'GRAE', 'date': 20220127, 
            'lat': 48.121, 'lon': 11.425, 'alt': 556, 'serial_number': 115
        }, {
            'sensor': 'mc', 'location': 'GRAE', 'date': 20220404, 
            'lat': 48.121, 'lon': 11.425, 'alt': 556, 'serial_number': 115
        }
    ]
    """
