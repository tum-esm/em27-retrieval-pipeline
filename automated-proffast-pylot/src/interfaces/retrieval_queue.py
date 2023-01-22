from datetime import datetime
import json
import os
import re
from typing import Iterator, Optional

from pydantic import BaseModel
from src import utils, custom_types, interfaces
from src.interfaces.pylot_factory import PylotFactory

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
MANUAL_QUEUE_FILE = f"{PROJECT_DIR}/config/manual-queue.json"


class SensorDate(BaseModel):
    sensor_id: str
    date: str


class ManualQueueItem(BaseModel):
    sensor_data_context: custom_types.SensorDataContext
    priority: int


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
    1. Takes all items from manual-queue.json with a priority > 0
    2. Takes all dates from the config.data_src_dirs.interferograms
    3. Takes all items from manual-queue.json with a priority < 0
    """

    def __init__(
        self,
        config: custom_types.Config,
        logger: utils.Logger,
        pylot_factory: PylotFactory,
    ):
        self.logger, self.config = logger, config
        self.location_data = interfaces.load_remote_location_data(
            github_repository=self.config.location_data.github_repository,
            access_token=self.config.location_data.access_token,
        )

        # TODO: make factory opinionated
        self.factory = pylot_factory

        SensorId = (str,)
        DateString = str
        self.processed_data: dict[SensorId, list[DateString]] = {}

    def __iter__(self) -> Iterator[custom_types.SensorDataContext]:
        iteration_count = 0
        while True:
            iteration_count += 1
            self.logger.line()
            self.logger.debug(f"Scheduler: Iteration {iteration_count}")

            next_manual_item = self._next_item_from_manual_queue()
            next_storage_item = self._next_item_from_storage_directory()

            if (next_manual_item is None) and (next_storage_item is not None):
                self.logger.info("Scheduler: Taking next item from storage directory")
                self._mark_as_processed(
                    next_storage_item.sensor_id,
                    next_storage_item.date,
                )
                yield next_storage_item
                continue

            if (next_manual_item is not None) and (next_storage_item is None):
                self.logger.info("Scheduler: Taking next item from manual queue")
                self._mark_as_processed(
                    next_manual_item.sensor_data_context.sensor_id,
                    next_manual_item.sensor_data_context.date,
                )
                yield next_manual_item.sensor_data_context
                continue

            if (next_manual_item is not None) and (next_storage_item is not None):
                if next_manual_item.priority > 0:
                    self.logger.info(
                        "Scheduler: Taking next item from manual queue (high priority"
                    )
                    self._mark_as_processed(
                        next_manual_item.sensor_data_context.sensor_id,
                        next_manual_item.sensor_data_context.date,
                    )
                    yield next_manual_item.sensor_data_context
                    continue
                else:
                    self.logger.info(
                        "Scheduler: Taking next item from storage directory"
                    )
                    self._mark_as_processed(
                        next_storage_item.sensor_id,
                        next_storage_item.date,
                    )
                    yield next_storage_item
                    continue

            # both queue (manual and storage) are empty
            self.logger.debug("Scheduler: no more items")
            break

    def _next_item_from_storage_directory(
        self,
    ) -> Optional[custom_types.SensorDataContext]:
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
                if self._is_marked_as_processed(sensor_id, date):
                    continue

                # do not consider if outputs exist or out of filter range
                if (
                    (self.config.data_filter.start_date > date)
                    or (self.config.data_filter.end_date < date)
                    or self.outputs_exist(sensor_id, date)
                ):
                    self._mark_as_processed(sensor_id, date)
                    continue

                # do not consider if there is no location data
                try:
                    sensor_data_context = self.location_data.get_sensor_data_context(
                        sensor_id, date
                    )
                except AssertionError as a:
                    self.logger.debug(str(a))
                    self._mark_as_processed(sensor_id, date)
                    continue

                # skip this date right now it upload is incomplete
                # or date is too recent -> this might change during
                # the current execution, hence it will not be marked
                # as being processed
                if (
                    self.date_is_too_recent(date)
                    or self.upload_is_incomplete(sensor_id, date)
                    or (not self.ifgs_exist(sensor_id, date))
                ):
                    continue

                return sensor_data_context

        return None

    def _next_item_from_manual_queue(
        self,
    ) -> Optional[ManualQueueItem]:
        """use the dates from manual-queue.json"""
        next_items = interfaces.ManualQueueInterface.get_items(self.logger)

        search_index = -1
        while True:
            search_index += 1
            try:
                next_item = next_items[search_index]
            except IndexError:
                return None

            if self._is_marked_as_processed(next_item.sensor_id, next_item.date):
                continue

            # do not consider if there is no location data
            try:
                sensor_data_context = self.location_data.get_sensor_data_context(
                    next_item.sensor_id, next_item.date
                )
            except AssertionError as a:
                self.logger.debug(str(a))
                self._mark_as_processed(next_item.sensor_id, next_item.date)
                continue

            # skip this date right now it upload is incomplete
            # -> this might change during the current execution,
            # hence it will not be marked as being processed
            if self.upload_is_incomplete(next_item.sensor_id, next_item.date) or (
                not self.ifgs_exist(next_item.sensor_id, next_item.date)
            ):
                continue

            return ManualQueueItem(
                sensor_data_context=sensor_data_context,
                priority=next_item.priority,
            )

    def _mark_as_processed(self, sensor_id: str, date: str) -> None:
        try:
            self.processed_sensor_dates[sensor_id].append(date)
        except KeyError:
            self.processed_sensor_dates[sensor_id] = [date]

    def _is_marked_as_processed(self, sensor_id: str, date: str) -> None:
        if sensor_id in self.processed_sensor_dates.keys():
            return date in self.processed_sensor_dates[sensor_id]
        return False

    def _ifgs_exist(self, sensor_id: str, date: str) -> bool:
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

    def _outputs_exist(self, sensor_id: str, date: str) -> bool:
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

    def _date_is_too_recent(self, date_string: str) -> bool:
        # will have the time 00:00:00
        date_object = datetime.strptime(date_string, "%Y%m%d")
        return (
            datetime.now() - date_object
        ).days < self.config.data_filter.min_days_delay

    def _upload_is_incomplete(self, sensor_id: str, date: str) -> bool:
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
