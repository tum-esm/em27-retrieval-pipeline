from datetime import datetime
import os
from src.utils import load_setup, LocationData, Logger

PROJECT_DIR, CONFIG = load_setup()


def _date_string_is_valid(date_string: str):
    try:
        now = datetime.now()
        then = datetime.strptime(date_string, "%Y%m%d")

        # the vertical profiles are only available with a 5 day delay
        assert (now - then).days >= 5

        return int(date_string) >= CONFIG["startDate"]
    except (AssertionError, ValueError, TypeError):
        return False


class RetrievalQueue:
    """
    Example queue:
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
        },
        ...
    ]
    """

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
                for x in os.listdir(f"{CONFIG['src']['interferograms']}/{s}_ifg")
                if len(x) >= 8 and _date_string_is_valid(x[:8])
            ]
            for d in ds:
                if len(d) > 8:
                    os.rename(
                        f"{CONFIG['src']['interferograms']}/{s}_ifg/{d}",
                        f"{CONFIG['src']['interferograms']}/{s}_ifg/{d[:8]}",
                    )
            data_directories[s] = list(sorted([int(d[:8]) for d in ds]))
        return data_directories

    def _generate_queue(self):
        l = LocationData()
        queue = []
        for sensor, sensor_dates in self.data_directories.items():
            for sensor_date in sensor_dates:
                location = l.get_location_for_date(sensor, sensor_date)
                if location is None:
                    Logger.warning(f"no location found for {sensor}/{sensor_date}")
                    continue

                queue.append(
                    {
                        "sensor": sensor,
                        "location": location,
                        "date": sensor_date,
                        **l.get_coordinates(location),
                        "serial_number": l.get_serial_number(sensor),
                    }
                )

        # take the most recent date first
        queue = list(sorted(queue, key=lambda x: x["date"], reverse=True))

        # take no more than 50 sensor-days at once
        if len(queue) > 50:
            queue = queue[:50]

        # TODO: Take items from the archive
        # archive_count = 50 - len(queue)

        return queue
