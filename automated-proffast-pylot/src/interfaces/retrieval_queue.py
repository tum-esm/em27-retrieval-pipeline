from datetime import datetime
import json
import os
import re
from typing import Optional
from pydantic import BaseModel
from src import utils, custom_types, interfaces


class ManualQueueItem(BaseModel):
    sensor_data_context: custom_types.SensorDataContext
    priority: int


class RetrievalQueue:
    """
    1. Takes all items from manual-queue.json with a priority > 0
    2. Takes all dates from the config.data_src_dirs.interferograms
    3. Takes all items from manual-queue.json with a priority < 0
    """

    def __init__(self, config: custom_types.Config, logger: utils.Logger):
        self.logger = logger
        self.config = config
        self.location_data = interfaces.load_remote_location_data(
            github_repository=self.config.location_data.github_repository,
            access_token=self.config.location_data.access_token,
        )

        self.processed_sensor_dates: dict[str, list[str]] = {}
        self.iteration_count = 0
        self.logger.info("RetrievalQueue is set up")

    def get_next_item(self) -> Optional[custom_types.SensorDataContext]:
        self.iteration_count += 1

        next_manual_item = self._next_item_from_manual_queue()
        next_storage_item = self._next_item_from_storage_directory()

        def process_scheduler_choice(
            choice: custom_types.SensorDataContext,
            source_label: str,
        ) -> None:
            self.logger.info(
                f"Scheduler iteration {self.iteration_count} - using {source_label}"
            )
            self._mark_as_processed(
                choice.sensor_id,
                choice.date,
            )

        if (next_manual_item is None) and (next_storage_item is not None):
            process_scheduler_choice(next_storage_item, "storage directory")
            return next_storage_item

        if (next_manual_item is not None) and (next_storage_item is None):
            process_scheduler_choice(
                next_manual_item.sensor_data_context, "manual queue"
            )
            return next_manual_item.sensor_data_context

        if (next_manual_item is not None) and (next_storage_item is not None):
            if next_manual_item.priority > 0:
                process_scheduler_choice(
                    next_manual_item.sensor_data_context, "manual queue (high priority)"
                )
                return next_manual_item.sensor_data_context
            else:
                process_scheduler_choice(next_storage_item, "storage directory")
                return next_storage_item

        # both queue (manual and storage) are empty
        return None

    def _next_item_from_storage_directory(
        self,
    ) -> Optional[custom_types.SensorDataContext]:
        """Use the dates from the storage directory"""

        # determine date_strings with data
        date_strings: list[str] = []
        for sensor_id in self.config.data_filter.sensor_ids_to_consider:
            sensor_ifgs_dir = os.path.join(
                self.config.data_src_dirs.interferograms, sensor_id
            )
            if not os.path.isdir(sensor_ifgs_dir):
                continue
            date_strings += [
                ds
                for ds in os.listdir(
                    os.path.join(self.config.data_src_dirs.interferograms, sensor_id)
                )
                if utils.is_date_string(ds)
            ]
        date_strings = list(sorted(set(date_strings), reverse=True))

        for date in date_strings:
            for sensor_id in self.config.data_filter.sensor_ids_to_consider:
                if self._is_marked_as_processed(sensor_id, date):
                    continue

                ifgs_missing_or_incomplete = lambda: (
                    not self._ifgs_exist(sensor_id, date)
                ) or (not self._upload_is_complete(sensor_id, date))
                outputs_exist = lambda: self._outputs_exist(sensor_id, date)
                date_too_recent = lambda: self._date_is_too_recent(date)
                date_out_of_filter_range = lambda: (
                    self.config.data_filter.start_date > date
                ) or (self.config.data_filter.end_date < date)

                # do not consider if outputs exist or out of filter range
                if outputs_exist():
                    self._mark_as_processed(sensor_id, date)
                    continue

                # skip this date right now it upload is incomplete
                # or date is too recent -> this might change during
                # the current execution, hence it will not be marked
                # as being processed
                if (
                    ifgs_missing_or_incomplete()
                    or date_too_recent()
                    or date_out_of_filter_range()
                ):
                    continue

                # do not consider if there is no location data
                try:
                    return self.location_data.get_sensor_data_context(sensor_id, date)
                except AssertionError as a:
                    self.logger.debug(str(a))
                    self._mark_as_processed(sensor_id, date)
                    continue

        return None

    def _next_item_from_manual_queue(self) -> Optional[ManualQueueItem]:
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

            # skip this date right now it upload is incomplete
            # -> this might change during the current execution,
            # hence it will not be marked as being processed
            ifgs_missing_or_incomplete = lambda: (
                not self._ifgs_exist(next_item.sensor_id, next_item.date)
            ) or (not self._upload_is_complete(next_item.sensor_id, next_item.date))
            if ifgs_missing_or_incomplete():
                continue

            # do not consider if there is no location data
            try:
                return ManualQueueItem(
                    sensor_data_context=self.location_data.get_sensor_data_context(
                        next_item.sensor_id, next_item.date
                    ),
                    priority=next_item.priority,
                )
            except AssertionError as a:
                self.logger.debug(str(a))
                self._mark_as_processed(next_item.sensor_id, next_item.date)
                continue

    def _mark_as_processed(self, sensor_id: str, date: str) -> None:
        try:
            self.processed_sensor_dates[sensor_id].append(date)
        except KeyError:
            self.processed_sensor_dates[sensor_id] = [date]

    def _is_marked_as_processed(self, sensor_id: str, date: str) -> bool:
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

        expected_ifg_pattern = re.compile(f"^{sensor_id}" + r"\d{8}.*\.ifg\.\d+$")
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
                self.config.data_dst_dirs.results,
                "proffast-2.2-outputs",
                sensor_id,
                "successful",
                date,
            )
        )
        failed_output_exists = os.path.isdir(
            os.path.join(
                self.config.data_dst_dirs.results,
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

    def _upload_is_complete(self, sensor_id: str, date: str) -> bool:
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
