from datetime import datetime
import json
import os
import re
from typing import Iterator, Optional

from pydantic import BaseModel
from src import utils, custom_types
from src.custom_types.pylot_factory import PylotFactory

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
MANUAL_QUEUE_FILE = f"{PROJECT_DIR}/config/manual-queue.json"


class SensorDate(BaseModel):
    sensor_id: str
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

    def __init__(
        self,
        config: custom_types.Config,
        logger: utils.Logger,
        pylot_factory: PylotFactory,
    ):
        self.config = config
        self.processed_sensor_dates: dict[str, list[str]] = {}
        self.location_data = utils.LocationData(config)
        self.factory = pylot_factory
        self.logger = logger

    def __iter__(self) -> Iterator[custom_types.SessionDict]:
        iteration_count = 0
        while True:
            iteration_count += 1
            self.logger.line()
            self.logger.debug(f"Scheduler: Iteration {iteration_count}")

            next_high_prio_queue_item = self._next_item_from_manual_queue(
                consider_priority_items=True
            )
            if next_high_prio_queue_item is not None:
                self.logger.info(
                    "Scheduler: Taking next item from manual queue (high priority)"
                )
                yield self._generate_session_dict(**next_high_prio_queue_item)
                continue
            else:
                self.logger.debug("Scheduler: High priority queue is empty")

            if self.config["process_uploads_automatically"]:
                next_upload_directory_item = self._next_item_from_upload_directory()
                if next_upload_directory_item is not None:
                    self.logger.info(
                        "Scheduler: Taking next item from upload directory"
                    )
                    yield self._generate_session_dict(**next_upload_directory_item)
                    continue
                else:
                    self.logger.debug("Scheduler: Upload directory is empty")
            else:
                self.logger.debug(
                    "Scheduler: Skipping upload queue (processUploadsAutomatically == false)"
                )

            next_low_prio_queue_item = self._next_item_from_manual_queue(
                consider_priority_items=False
            )
            if next_low_prio_queue_item is not None:
                self.logger.info(
                    "Scheduler: Taking next item from manual queue (low priority)"
                )
                yield self._generate_session_dict(**next_low_prio_queue_item)
                continue
            else:
                self.logger.debug("Scheduler: Low priority queue is empty")

            break

    def _generate_session_dict(
        self, sensor: str, date: str
    ) -> custom_types.SessionDict:
        self.processed_sensor_dates[sensor].append(date)

        location = self.location_data.get_location_for_date(sensor, date)
        utc_offset = self.location_data.get_utc_offset_for_date(sensor, date)
        assert location is not None, f"location for {sensor}/{date} is unknown"
        assert utc_offset is not None, f"utc_offset for {sensor}/{date} is unknown"

        coordinates_dict = self.location_data.get_coordinates_for_location(location)
        serial_number = self.location_data.get_serial_number_for_sensor(sensor)
        # Create new container for session
        container_id = self.factory.create_pylot_instance()
        container_path = self.factory.containers[container_id]

        return {
            "sensor": sensor,
            "location": location,
            "date": date,
            "lat": coordinates_dict["lat"],
            "lon": coordinates_dict["lon"],
            "alt": coordinates_dict["alt"],
            "serial_number": serial_number,
            "utc_offset": utc_offset,
            "container_id": container_id,
            "container_path": container_path,
        }

    def _next_item_from_storage_directory(self) -> Optional[SensorDate]:
        """Use the dates from the storage directory"""

        # determine date_strings with data
        date_strings: list[str] = []
        for sensor in self.config.data_filter.sensor_ids_to_consider:
            date_strings += [
                ds
                for ds in os.path.join(self.config.data_src_dirs.interferograms, sensor)
                if utils.is_date_string(ds)
            ]
        date_strings = list(sorted(set(date_strings), reverse=True))

        for date in date_strings:
            for sensor_id in self.config.data_filter.sensor_ids_to_consider:
                # TODO: continue if marked as processed

                if (
                    self.outputs_exist(sensor_id, date)
                    # location data does not exist
                    # utc offset does not exist
                ):
                    # TODO: mark as processed
                    continue

                if (
                    (self.config.data_filter.start_date > date)
                    or (self.config.data_filter.end_date < date)
                    or self.date_is_too_recent(date)
                    or self.upload_is_incomplete(sensor_id, date)
                    or self.ifgs_exist(sensor_id, date)
                ):
                    continue

                # TODO: mark as processed
                return SensorDate(sensor_id=sensor_id, date=date)

        return None

    def _next_item_from_manual_queue(
        self, consider_priority_items: bool = True
    ) -> Optional[SensorDateDict]:
        """
        Use the dates from manual-queue.json
        """

        try:
            with open(MANUAL_QUEUE_FILE, "r") as f:
                manual_queue: list[custom_types.ManualQueueItemDict] = json.load(f)
                custom_types.validate_manual_queue(manual_queue, self.config)
        except Exception as e:
            self.logger.warning(f"Manual queue in an invalid format: {e}")
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
                self.logger.debug(f"Scheduler: Skipping {sensor}/{date} ({e})")
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
        sensor: str, date: str, config: custom_types.ConfigDict, logger: utils.Logger
    ) -> None:
        if not os.path.isfile(MANUAL_QUEUE_FILE):
            return

        with open(MANUAL_QUEUE_FILE, "r") as f:
            old_manual_queue: list[custom_types.ManualQueueItemDict] = json.load(f)
            custom_types.validate_manual_queue(old_manual_queue, config)

        new_manual_queue = list(
            filter(
                lambda x: not ((x["sensor"] == sensor) and (x["date"] == date)),
                old_manual_queue,
            )
        )
        if len(new_manual_queue) < len(old_manual_queue):
            logger.debug(f"Removing item {sensor}/{date} from manual queue")
            with open(MANUAL_QUEUE_FILE, "w") as f:
                json.dump(new_manual_queue, f, indent=4)

    def ifgs_exist(self, sensor_id: str, date: str) -> bool:
        """for a given sensor_id and date, determine whether the
        interferograms exist in the src directory"""
        ifg_src_directory = os.path.join(
            self.config.data_src_dirs.interferograms,
            sensor_id,
            date,
        )
        if not os.path.isdir(ifg_src_directory):
            return False

        expected_ifg_pattern = re.compile(f"^{sensor_id}\\d{{8}}.*\\.ifg\\.\d+$")
        ifg_file_count = len(
            [
                f
                for f in os.listdir(ifg_src_directory)
                if expected_ifg_pattern.match(f) is not None
            ]
        )
        return ifg_file_count > 0

    def outputs_exist(self, sensor_id: str, date: str) -> bool:
        """for a given sensor_id and date, determine whether the
        outputs exist in the src directory"""
        successful_output_exists = os.path.isdir(
            os.path.join(
                self.config.data_dst.results_dir,
                "proffast-2.2-outputs",
                sensor_id,
                "successful",
                date,
            )
        )
        failed_output_exists = os.path.isdir(
            os.path.join(
                self.config.data_dst.results_dir,
                "proffast-2.2-outputs",
                sensor_id,
                "failed",
                date,
            )
        )
        return successful_output_exists or failed_output_exists

    def date_is_too_recent(self, date_string: str) -> bool:
        # will have the time 00:00:00
        date_object = datetime.strptime(date_string, "%Y%m%d")
        return (
            datetime.now() - date_object
        ).days < self.config.data_filter.min_days_delay

    def upload_is_incomplete(self, sensor_id: str, date: str) -> bool:
        """
        If the dir_path contains a file "upload-meta.json", then this
        function returns whether the internally used format indicates
        a completed upload. Otherwise it will just return True
        """
        upload_meta_path = os.path.join(
            self.config.data_src_dirs.interferograms,
            sensor_id,
            date,
            "upload-meta.json",
        )
        if not os.path.isfile(upload_meta_path):
            return True

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
