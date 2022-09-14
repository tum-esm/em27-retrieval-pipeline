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
    start_date: Optional[str] = None,
    min_days_delay: int = 1,
) -> bool:
    date_object = datetime.strptime(
        date_string, "%Y%m%d"
    )  # will have the time 00:00:00
    try:
        assert (datetime.now() - date_object).days >= min_days_delay
        if start_date is not None:
            assert date_string >= start_date
        return True
    except AssertionError:
        return False


def _date_string_is_valid(date_string: str) -> bool:
    try:
        datetime.strptime(date_string, "%Y%m%d")
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
        self.location_data = utils.LocationData(config)

    def __iter__(self) -> Iterator[types.SessionDict]:
        iteration_count = 0
        while True:
            iteration_count += 1
            utils.Logger.line()
            utils.Logger.debug(f"Scheduler: Iteration {iteration_count}")

            next_high_prio_queue_item = self._next_item_from_manual_queue(
                consider_priority_items=True
            )
            if next_high_prio_queue_item is not None:
                utils.Logger.info(
                    "Scheduler: Taking next item from manual queue (high priority)"
                )
                yield self._generate_session_dict(**next_high_prio_queue_item)
                continue
            else:
                utils.Logger.debug("Scheduler: High priority queue is empty")

            if self.config["process_uploads_automatically"]:
                next_upload_directory_item = self._next_item_from_upload_directory()
                if next_upload_directory_item is not None:
                    utils.Logger.info(
                        "Scheduler: Taking next item from upload directory"
                    )
                    yield self._generate_session_dict(**next_upload_directory_item)
                    continue
                else:
                    utils.Logger.debug("Scheduler: Upload directory is empty")
            else:
                utils.Logger.debug(
                    "Scheduler: Skipping upload queue (processUploadsAutomatically == false)"
                )

            next_low_prio_queue_item = self._next_item_from_manual_queue(
                consider_priority_items=False
            )
            if next_low_prio_queue_item is not None:
                utils.Logger.info(
                    "Scheduler: Taking next item from manual queue (low priority)"
                )
                yield self._generate_session_dict(**next_low_prio_queue_item)
                continue
            else:
                utils.Logger.debug("Scheduler: Low priority queue is empty")

            break

    def _generate_session_dict(self, sensor: str, date: str) -> types.SessionDict:
        self.processed_sensor_dates[sensor].append(date)

        location = self.location_data.get_location_for_date(sensor, date)
        assert location is not None, f"location for {sensor}/{date} is unknown"

        coordinates_dict = self.location_data.get_coordinates_for_location(location)
        serial_number = self.location_data.get_serial_number_for_sensor(sensor)

        return {
            "sensor": sensor,
            "location": location,
            "date": date,
            "lat": coordinates_dict["lat"],
            "lon": coordinates_dict["lon"],
            "alt": coordinates_dict["alt"],
            "serial_number": serial_number,
        }

    def _pyra_upload_is_complete(self, sensor: str, date: str) -> Optional[bool]:
        """
        If the dir_path contains a file "upload-meta.json", then this function
        returns the boolean value of meta.complete and raises an exception if
        that field is not found or not a boolean.

        If there is no "upload-meta.json" file, the this function returns None.
        """
        upload_meta_path = os.path.join(
            self.config["src"]["interferograms"]["upload"],
            sensor,
            date,
            "upload-meta.json",
        )
        if not os.path.isfile(upload_meta_path):
            return None

        try:
            with open(upload_meta_path) as f:
                upload_meta = json.load(f)
            pyra_upload_is_complete = upload_meta["complete"]
            assert isinstance(
                pyra_upload_is_complete, bool
            ), "upload-meta.complete is not a boolean"
            return pyra_upload_is_complete
        except Exception as e:
            raise Exception(f'upload-meta.json at "{upload_meta_path}" is invalid: {e}')

    def _next_item_from_upload_directory(self) -> Optional[SensorDateDict]:
        """
        Use the dates from upload src directory
        """
        sensor_dates: list[SensorDateDict] = []
        for sensor in self.config["sensors_to_consider"]:
            for date in os.listdir(
                os.path.join(self.config["src"]["interferograms"]["upload"], sensor)
            ):
                if any(
                    [
                        (date in self.processed_sensor_dates.get(sensor, [])),
                        (not _date_string_is_valid(date)),
                    ]
                ):
                    continue

                try:
                    assert _consider_date_string(
                        date, min_days_delay=5
                    ), "too recent date"

                    assert self._pyra_upload_is_complete(sensor, date) in [
                        True,
                        None,
                    ], "pyra upload incomplete"

                    assert (
                        self.location_data.get_location_for_date(sensor, date)
                        is not None
                    ), "no location data"

                except AssertionError as e:
                    utils.Logger.debug(f"Scheduler: Skipping {sensor}/{date} ({e})")
                    self._mark_as_processed(sensor, date)
                    continue

                sensor_dates.append({"sensor": sensor, "date": date})

        if len(sensor_dates) == 0:
            return None

        s = max(sensor_dates, key=lambda x: x["date"])
        self._mark_as_processed(**s)
        return s

    def _next_item_from_manual_queue(
        self, consider_priority_items: bool = True
    ) -> Optional[SensorDateDict]:
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

            if any(
                [
                    (date in self.processed_sensor_dates.get(sensor, [])),
                    (priority > 0 and (not consider_priority_items)),
                    (priority < 0 and (consider_priority_items)),
                ]
            ):
                continue

            try:
                assert _consider_date_string(date, min_days_delay=1), "too recent date"

                assert self._pyra_upload_is_complete(sensor, date) in [
                    True,
                    None,
                ], "pyra upload incomplete"

                assert (
                    self.location_data.get_location_for_date(sensor, date) is not None
                ), "no location data"

            except AssertionError as e:
                utils.Logger.debug(f"Scheduler: Skipping {sensor}/{date} ({e})")
                self._mark_as_processed(sensor, date)
                continue

            sensor_dates.append({"sensor": sensor, "date": date})

        if len(sensor_dates) == 0:
            return None

        self._mark_as_processed(**sensor_dates[0])
        return sensor_dates[0]

    def _mark_as_processed(self, sensor: str, date: str) -> None:
        try:
            self.processed_sensor_dates[sensor].append(date)
        except KeyError:
            self.processed_sensor_dates[sensor] = [date]

    @staticmethod
    def remove_from_queue_file(
        sensor: str, date: str, config: types.ConfigDict
    ) -> None:
        if not os.path.isfile(MANUAL_QUEUE_FILE):
            return

        with open(MANUAL_QUEUE_FILE, "r") as f:
            old_manual_queue: list[types.ManualQueueItemDict] = json.load(f)
            types.validate_manual_queue(old_manual_queue, config)

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
