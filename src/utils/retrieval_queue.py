from datetime import datetime
import json
import os
import cerberus

from requests import JSONDecodeError
from src.utils import load_setup, LocationData, Logger

PROJECT_DIR, CONFIG = load_setup()


manual_queue_validator = cerberus.Validator(
    {
        "queue": {
            "type": "list",
            "schema": {
                "type": "dict",
                "schema": {
                    "sensor": {"type": "string"},
                    "date": {"type": "string"},
                    "priority": {"type": "integer", "forbidden": [0]},
                },
            },
        }
    }
)
location_data = LocationData()


def _date_string_is_valid(date_string: str, consider_config_start_date: bool = True):
    try:
        now = datetime.now()
        then = datetime.strptime(date_string, "%Y%m%d")

        # the vertical profiles are only available with a 5 day delay
        assert (now - then).days >= 5

        if consider_config_start_date:
            assert int(date_string) >= CONFIG["startDate"]

        return True
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

    1. Takes all items from manual-queue.json with a priority > 0
    2. Takes all dates from /mnt/measurementData/mu
    3. Takes all items from manual-queue.json with a priority < 0
    """

    def __init__(self, sensor_names: list[str]):
        self.sensor_names = sensor_names

    def __iter__(self):
        iteration_count = 0
        while True:
            iteration_count += 1
            if iteration_count > 50:
                Logger.info("Scheduler: Already processed 50 items in this execution.")
                return

            next_high_prio_queue_item = self._next_item_from_manual_queue(priority=True)
            if next_high_prio_queue_item is not None:
                Logger.info(
                    "Scheduler: Taking next item from manual queue (high priority)"
                )
                yield next_high_prio_queue_item
                continue

            next_upload_directory_item = self._next_item_from_upload_directory(self)
            if next_upload_directory_item is not None:
                Logger.info("Scheduler: Taking next item from upload directory")
                yield next_upload_directory_item
                continue

            next_low_prio_queue_item = self._next_item_from_manual_queue(priority=False)
            if next_low_prio_queue_item is not None:
                Logger.info(
                    "Scheduler: Taking next item from manual queue (high priority)"
                )
                yield next_low_prio_queue_item
                continue

            return

    def _next_item_from_upload_directory(self):
        """
        Use the dates from /mnt/measurementData/mu
        """
        sensor_dates = []
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
            sensor_dates += [{"sensor": s, "date": d} for d in ds]

        if len(sensor_dates) == 0:
            return None
        else:
            return RetrievalQueue._generate_process_from_sensor_date(
                list(sorted(sensor_dates, key=lambda x: x["date"], reverse=True))[0]
            )

    def _next_item_from_manual_queue(self, priority: bool = True):
        """
        Use the dates from manual-queue.json
        """

        try:
            with open(f"{PROJECT_DIR}/manual-queue.json", "r") as f:
                manual_queue_content = json.load(f)
            assert manual_queue_validator.validate(
                sensor_dates
            ), manual_queue_validator.errors

            for x in sensor_dates:
                assert (
                    x["sensor"] in self.sensor_names
                ), f"no coordinates found for sensor \"{x['sensor']}\""
                assert _date_string_is_valid(
                    x["date"], consider_config_start_date=False
                ), f"\"{x['date']}\" is not a valid date"
        except AssertionError as e:
            Logger.warning(f"Manual queue in an invalid format: {e}")
            return None
        except JSONDecodeError:
            Logger.warning(f"Manual queue in an invalid JSON format")
            return None
        except FileNotFoundError:
            return None

        # priority 0 is not allowed in schema, (0 is the regular queue from /mnt/...)
        sensor_dates = list(
            filter(
                lambda x: (x["priority"] > 0) if priority else (x["priority"] < 0),
                manual_queue_content,
            )
        )

        if len(sensor_dates) == 0:
            return None
        else:
            # Highest priority first. With the same
            # priority, it prefers the latest dates
            sensor_dates = list(
                sorted(
                    sensor_dates,
                    key=lambda x: f'{str(x["priority"]).zfill(10)}{x["date"]}',
                    reverse=True,
                )
            )
            return RetrievalQueue._generate_process_from_sensor_date(
                {
                    "sensor": sensor_dates[0]["sensor"],
                    "date": sensor_dates[0]["date"],
                }
            )

    def _generate_process_from_sensor_date(self, sensor_date: dict):
        sensor = sensor_date["sensor"]
        date = int(sensor_date["date"])
        location = location_data.get_location_for_date(sensor, date)
        coordinates_dict = location_data.get_coordinates(location)
        serial_number = location_data.get_serial_number(sensor)

        return {
            "sensor": sensor,
            "location": location,
            "date": date,
            **coordinates_dict,
            "serial_number": serial_number,
        }
