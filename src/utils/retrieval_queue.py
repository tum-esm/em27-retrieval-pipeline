from datetime import datetime
import json
import os
from typing import Iterator, Optional, TypedDict
from src import utils, types
from src.types import manual_queue

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
MANUAL_QUEUE_FILE = f"{PROJECT_DIR}/config/manual-queue.json"


class SensorDateDict(TypedDict):
    sensor: str
    date: str


def _consider_date_string(
    date_string: str,
    start_date: str = None,
    min_days_delay: int = 1,
):
    try:
        now = datetime.now()
        then = datetime.strptime(date_string, "%Y%m%d")  # will have the time 00:00:00

        assert (now - then).days >= min_days_delay

        if start_date is not None:
            assert date_string >= start_date

        return True
    except (AssertionError, ValueError):
        return False


class RetrievalQueue:
    """
    Example queue:
    [
        {
            'sensor': 'mb', 'location': 'FEL', 'date': '20220512',
            'lat': 48.148, 'lon': 11.73, 'alt': 536, 'serial_number': 86
        }, {
            'sensor': 'mb', 'location': 'FEL', 'date': '20220513',
            'lat': 48.148, 'lon': 11.73, 'alt': 536, 'serial_number': 86
        }, {
            'sensor': 'mb', 'location': 'TUM_I', 'date': '20220514',
            'lat': 48.151, 'lon': 11.569, 'alt': 539, 'serial_number': 86
        },
        ...
    ]

    1. Takes all items from manual-queue.json with a priority > 0
    2. Takes all dates from /mnt/measurementData/mu
    3. Takes all items from manual-queue.json with a priority < 0
    """

    def __init__(self, config: types.ConfigDict):
        self.config = config
        self.processed_sensor_dates: dict[str, list[str]] = {
            s: [] for s in config["sensors_to_consider"]
        }
        self.location_data = utils.LocationData()

    def __iter__(self) -> Iterator[types.SessionDict]:
        iteration_count = 0
        while True:
            iteration_count += 1
            utils.Logger.line()
            utils.Logger.debug(f"Scheduler: Iteration {iteration_count}")

            next_high_prio_queue_item = self._next_item_from_manual_queue(priority=True)
            if next_high_prio_queue_item is not None:
                utils.Logger.info(
                    "Scheduler: Taking next item from manual queue (high priority)"
                )
                yield next_high_prio_queue_item
                continue
            else:
                utils.Logger.debug("Scheduler: High priority queue is empty")

            if self.config["processUploadsAutomatically"]:
                next_upload_directory_item = self._next_item_from_upload_directory()
                if next_upload_directory_item is not None:
                    utils.Logger.info(
                        "Scheduler: Taking next item from upload directory"
                    )
                    yield next_upload_directory_item
                    continue
                else:
                    utils.Logger.debug("Scheduler: Upload directory is empty")
            else:
                utils.Logger.debug(
                    "Scheduler: Skipping upload queue (processUploadsAutomatically == false)"
                )

            next_low_prio_queue_item = self._next_item_from_manual_queue(priority=False)
            if next_low_prio_queue_item is not None:
                utils.Logger.info(
                    "Scheduler: Taking next item from manual queue (low priority)"
                )
                yield next_low_prio_queue_item
                continue
            else:
                utils.Logger.debug("Scheduler: Low priority queue is empty")

            return

    def _generate_session_dict(self, sensor: str, date: str) -> types.SessionDict:
        self.processed_sensor_dates[sensor].append(date)

        location = self.location_data.get_location_for_date(sensor, date)
        coordinates_dict = self.location_data.get_coordinates(location)
        serial_number = self.location_data.get_serial_number(sensor)

        return {
            "sensor": sensor,
            "location": location,
            "date": date,
            **coordinates_dict,
            "serial_number": serial_number,
        }

    # TODO: Only consider dates from upload dir where upload has been finished
    # def _pyra_upload_is_complete(self, dir_path: str) -> Optional[bool]:
    #    """
    #    If the dir_path contains a file "upload-meta.json", then this function
    #    returns the boolean value of meta.complete and raises an exception if
    #    that field is not found or not a boolean.
    #
    #    If there is no "upload-meta.json" file, the this function returns None.
    #    """
    #    upload_meta_path = os.path.join(dir_path, "upload-meta.json")
    #    if not os.path.isfile(upload_meta_path):
    #        return None
    #
    #    try:
    #        with open(upload_meta_path) as f:
    #            upload_meta = json.load(f)
    #        pyra_upload_is_complete = upload_meta["complete"]
    #        assert isinstance(
    #            pyra_upload_is_complete, bool
    #        ), "upload-meta.complete is not a boolean"
    #        return pyra_upload_is_complete
    #    except Exception as e:
    #        raise Exception(f'upload-meta.json at "{upload_meta_path}" is invalid: {e}')

    def _next_item_from_upload_directory(self) -> Optional[SensorDateDict]:
        """
        Use the dates from /mnt/measurementData/mu
        """
        sensor_dates: list[SensorDateDict] = []
        for sensor in self.config["sensors_to_consider"]:
            upload_src = os.path.join(
                self.config["src"]["interferograms"]["upload"], sensor
            )
            for date in os.listdir(upload_src):
                if not _consider_date_string(
                    date, start_date=self.config["start_date"], min_days_delay=5
                ):
                    continue

                if date in self.processed_sensor_dates.get(sensor, []):
                    continue

                # TODO: Only consider dates from upload dir where upload has been finished

                sensor_dates.append({"sensor": sensor, "date": date})

        if len(sensor_dates) == 0:
            return None

        return max(sensor_dates, key=lambda x: x["date"])

    def _next_item_from_manual_queue(
        self, consider_priority_items: bool = True
    ) -> Optional[types.SessionDict]:
        """
        Use the dates from manual-queue.json
        """

        try:
            with open(MANUAL_QUEUE_FILE, "r") as f:
                manual_queue: list[types.ManualQueueItemDict] = json.load(f)
                types.validate_manual_queue(manual_queue, self.config)
        except Exception as e:
            utils.Logger.warning(f"Manual queue in an invalid format: {e}")
            return None

        # highest priority first then latest date first
        manual_queue = list(
            sorted(
                manual_queue, key=lambda x: f'{x["priority"]}{x["date"]}', reverse=True
            )
        )

        sensor_dates: list[SensorDateDict] = []

        for manual_queue_item in manual_queue:
            sensor = manual_queue_item["sensor"]
            date = manual_queue_item["date"]
            priority = manual_queue_item["priority"]

            if date in self.processed_sensor_dates.get(sensor, []):
                continue

            if (priority > 0 and (not consider_priority_items)) or (
                priority < 0 and (consider_priority_items)
            ):
                continue

            # TODO: Only consider dates from upload dir where upload has been finished

            if not _consider_date_string(date, min_days_delay=1):
                utils.Logger.debug(
                    f"Scheduler: Skipping {sensor}/{date} (invalid or too recent date)"
                )
                self._mark_sensor_date_as_processed(sensor, date)

            sensor_dates.append({"sensor": sensor, "date": date})

        return None if (len(sensor_dates) == 0) else sensor_dates[0]

    @staticmethod
    def remove_date_from_queue(sensor: str, date: str):
        if not os.path.isfile(MANUAL_QUEUE_FILE):
            return

        with open(MANUAL_QUEUE_FILE, "r") as f:
            old_manual_queue: list[types.ManualQueueItemDict] = json.load(f)
            types.validate_manual_queue(old_manual_queue)

        new_manual_queue = list(
            filter(
                lambda x: not ((x["sensor"] == sensor) and (x["date"] == date)),
                old_manual_queue,
            )
        )
        if len(new_manual_queue) < len(old_manual_queue):
            utils.Logger.debug(f"Removing item {sensor}/{date} from manual queue")
            with open(MANUAL_QUEUE_FILE, "w") as f:
                json.dump(new_manual_queue, f, indent=4)
