from datetime import datetime
import json
import os
from typing import Iterator, Optional, TypedDict
from src import utils, types

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
        self.processed_sensor_dates: dict[str, list[str]] = {}
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

    # TODO: Only consider dates from upload dir where upload has been finished
    def _next_item_from_upload_directory(self) -> Optional[types.SessionDict]:
        """
        Use the dates from /mnt/measurementData/mu
        """
        sensor_dates = []
        for sensor in self.config["sensorsToConsider"]:
            upload_src = self.config["src"]["interferograms"]["upload"][sensor]
            dates = [
                x
                for x in os.listdir(upload_src)
                if _consider_date_string(
                    x, start_date=self.config["start_date"], min_days_delay=5
                )
            ]
            sensor_dates += [{"sensor": sensor, "date": date} for date in dates]

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
            utils.Logger.error(
                f'Error during "_generate_process_from_sensor_date" '
                + "for next_sensor_date={next_sensor_date}"
            )
            utils.Logger.exception()
            return self._next_item_from_upload_directory()

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

        sensor_dates: list[SensorDateDict] = []

        for manual_queue_item in manual_queue:
            sensor = manual_queue_item["sensor"]
            date = manual_queue_item["date"]
            priority = manual_queue_item["priority"]

            if not _consider_date_string(date, min_days_delay=1):
                utils.Logger.debug(
                    f"Scheduler: Skipping {sensor}/{date} "
                    + "(invalid or too recent date)"
                )
                self._mark_sensor_date_as_processed(sensor, date)

            if date in self.processed_sensor_dates.get(sensor, []):
                continue

            if (priority > 0 and (not consider_priority_items)) or (
                priority < 0 and (consider_priority_items)
            ):
                continue

            sensor_dates.append({"sensor": sensor, "date": date})

        # TODO: CONTINUE HERE

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
            sensor, date = sensor_date["sensor"], sensor_date["date"]
            self._mark_sensor_date_as_processed(sensor, date)
            return self._generate_process_from_sensor_date(
                {
                    "sensor": sensor,
                    "date": date,
                }
            )

    def _mark_sensor_date_as_processed(self, sensor: str, date: str):
        if sensor not in self.processed_sensor_dates.keys():
            self.processed_sensor_dates[sensor] = [date]
        else:
            self.processed_sensor_dates[sensor].append(date)

    def _filter_sensor_dates_by_processed_items(
        self, sensor_dates: list[types.SessionDict]
    ):
        return list(
            filter(
                lambda x: x["date"]
                not in self.processed_sensor_dates.get(x["sensor"], []),
                sensor_dates,
            )
        )

    def _generate_process_from_sensor_date(
        self, sensor_date: dict
    ) -> types.SessionDict:
        sensor = sensor_date["sensor"]
        date = int(sensor_date["date"])
        location = self.location_data.get_location_for_date(sensor, date)
        assert location is not None, f"Please add location data for {sensor}/{date}."

        coordinates_dict = self.location_data.get_coordinates(location)
        serial_number = self.location_data.get_serial_number(sensor)

        return {
            "sensor": sensor,
            "location": location,
            "date": date,
            **coordinates_dict,
            "serial_number": serial_number,
        }

    @staticmethod
    def remove_date_from_queue(sensor: str, date: str):
        if not os.path.isfile(MANUAL_QUEUE_FILE):
            return

        with open(MANUAL_QUEUE_FILE, "r") as f:
            old_manual_queue_content = json.load(f)
        assert isinstance(old_manual_queue_content, list)

        new_manual_queue_content = list(
            filter(
                lambda x: not ((x["sensor"] == sensor) and (x["date"] == date)),
                old_manual_queue_content,
            )
        )
        if len(new_manual_queue_content) < len(old_manual_queue_content):
            utils.Logger.debug("Removing item from manual queue")
            with open(MANUAL_QUEUE_FILE, "w") as f:
                json.dump(new_manual_queue_content, f, indent=4)
