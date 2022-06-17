from datetime import datetime
import json
import os
import sys
import cerberus

from requests import JSONDecodeError
from src.utils import LocationData, Logger

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))


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


def _date_string_is_valid(date_string: str, start_date: str = None):
    try:
        now = datetime.now()
        then = datetime.strptime(date_string, "%Y%m%d")

        if start_date is not None:
            assert int(date_string) >= start_date

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

    def __init__(self, config: dict):
        self.config = config
        self.processed_sensor_dates = {}

    def __iter__(self):
        iteration_count = 0
        while True:
            iteration_count += 1
            Logger.line()
            Logger.debug(f"Scheduler: Iteration {iteration_count}")

            next_high_prio_queue_item = self._next_item_from_manual_queue(priority=True)
            if next_high_prio_queue_item is not None:
                Logger.info(
                    "Scheduler: Taking next item from manual queue (high priority)"
                )
                yield next_high_prio_queue_item
                continue
            else:
                Logger.debug("Scheduler: High priority queue is empty")

            if self.config["processUploadsAutomatically"]:
                next_upload_directory_item = self._next_item_from_upload_directory()
                if next_upload_directory_item is not None:
                    Logger.info("Scheduler: Taking next item from upload directory")
                    yield next_upload_directory_item
                    continue
                else:
                    Logger.debug("Scheduler: Upload directory is empty")
            else:
                Logger.debug(
                    "Scheduler: Skipping upload queue (processUploadsAutomatically == false)"
                )

            next_low_prio_queue_item = self._next_item_from_manual_queue(priority=False)
            if next_low_prio_queue_item is not None:
                Logger.info(
                    "Scheduler: Taking next item from manual queue (low priority)"
                )
                yield next_low_prio_queue_item
                continue
            else:
                Logger.debug("Scheduler: Low priority queue is empty")

            return

    # TODO: Only consider dates from upload dir where upload has been finished
    #       How to tell, whether an upload has been finished?
    def _next_item_from_upload_directory(self):
        """
        Use the dates from /mnt/measurementData/mu
        """
        sensor_dates = []
        for s in self.config["sensorsToConsider"]:
            upload_src = self.config["src"]["interferograms"]["upload"][s]
            ds = [
                x
                for x in os.listdir(upload_src)
                if len(x) >= 8
                and _date_string_is_valid(x[:8], start_date=self.config["startDate"])
            ]
            for d in ds:
                if len(d) > 8:
                    os.rename(
                        f"{upload_src}/{d}",
                        f"{upload_src}/{d[:8]}",
                    )
            sensor_dates += [{"sensor": s, "date": d} for d in ds]

        # Do not take in a sensor date multiple times
        sensor_dates = self._filter_sensor_dates_by_processed_items(sensor_dates)

        if len(sensor_dates) == 0:
            return None

        next_sensor_date = max(sensor_dates, key=lambda x: x["date"])
        self._mark_sensor_date_as_processed(
            next_sensor_date["sensor"], str(next_sensor_date["date"])
        )

        try:
            next_process = self._generate_process_from_sensor_date(next_sensor_date)
            return next_process
        except:
            Logger.error(
                f'Error during "_generate_process_from_sensor_date" '
                + "for next_sensor_date={next_sensor_date}"
            )
            Logger.exception()
            return self._next_item_from_upload_directory()

    def _next_item_from_manual_queue(self, priority: bool = True):
        """
        Use the dates from manual-queue.json
        """

        try:
            with open(f"{PROJECT_DIR}/manual-queue.json", "r") as f:
                sensor_dates = json.load(f)
            assert manual_queue_validator.validate(
                {"queue": sensor_dates}
            ), manual_queue_validator.errors

            for x in sensor_dates:
                assert (
                    x["sensor"] in self.config["sensorsToConsider"]
                ), f"no coordinates found for sensor \"{x['sensor']}\""
                assert _date_string_is_valid(
                    x["date"]
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
                sensor_dates,
            )
        )

        # Do not take in a sensor date multiple times
        sensor_dates = self._filter_sensor_dates_by_processed_items(sensor_dates)

        if len(sensor_dates) == 0:
            return None
        else:
            # Highest priority first. With the same
            # priority, it prefers the latest dates
            sensor_date = list(
                sorted(
                    sensor_dates,
                    key=lambda x: f'{str(x["priority"]).zfill(10)}{x["date"]}',
                    reverse=True,
                )
            )[0]
            self._mark_sensor_date_as_processed(
                sensor_date["sensor"], sensor_date["date"]
            )
            return self._generate_process_from_sensor_date(
                {
                    "sensor": sensor_date["sensor"],
                    "date": sensor_date["date"],
                }
            )

    def _mark_sensor_date_as_processed(self, sensor: str, date: str):
        if sensor not in self.processed_sensor_dates.keys():
            self.processed_sensor_dates[sensor] = [date]
        else:
            self.processed_sensor_dates[sensor].append(date)

    def _filter_sensor_dates_by_processed_items(self, sensor_dates: list):
        return list(
            filter(
                lambda x: x["date"]
                not in self.processed_sensor_dates.get(x["sensor"], []),
                sensor_dates,
            )
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

    @staticmethod
    def remove_date_from_queue(sensor: str, date: str):
        queue_file = f"{PROJECT_DIR}/manual-queue.json"
        if not os.path.isfile(queue_file):
            return

        with open(queue_file, "r") as f:
            old_manual_queue_content = json.load(f)
        assert isinstance(old_manual_queue_content, list)

        new_manual_queue_content = list(
            filter(
                lambda x: not ((x["sensor"] == sensor) and (x["date"] == date)),
                old_manual_queue_content,
            )
        )
        if len(new_manual_queue_content) < len(old_manual_queue_content):
            Logger.debug("Removing item from manual queue")
            with open(queue_file, "w") as f:
                json.dump(new_manual_queue_content, f, indent=4)
