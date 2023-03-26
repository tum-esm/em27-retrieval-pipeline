from datetime import datetime, timedelta
import json
import os
from typing import Optional
from pydantic import BaseModel
import tum_esm_em27_metadata
import tum_esm_utils
from src import utils, custom_types, interfaces


class ManualQueueItem(BaseModel):
    sensor_data_context: tum_esm_em27_metadata.types.SensorDataContext
    priority: int


class RetrievalQueue:
    """
    1. Takes all items from manual-queue.json with a priority > 0
    2. Takes all dates from the config.data_src_dirs.interferograms
    3. Takes all items from manual-queue.json with a priority < 0
    """

    def __init__(
        self,
        config: custom_types.Config,
        logger: utils.automated_proffast.Logger,
        em27_metadata: Optional[
            tum_esm_em27_metadata.interfaces.EM27MetadataInterface
        ] = None,
    ) -> None:

        """Initialize the retrieval queue. This includes loading the location
        data from GitHub using the package `tum_esm_em27_metadata`."""
        self.logger = logger
        self.config = config

        self.em27_metadata: tum_esm_em27_metadata.interfaces.EM27MetadataInterface

        if em27_metadata is not None:
            self.em27_metadata = em27_metadata
        else:
            self.em27_metadata = tum_esm_em27_metadata.load_from_github(
                github_repository=self.config.general.location_data.github_repository,
                access_token=self.config.general.location_data.access_token,
            )

        self.processed_sensor_dates: dict[str, list[str]] = {}
        self.iteration_count = 0
        self.logger.info("RetrievalQueue is set up")

    def get_next_item(self) -> Optional[tum_esm_em27_metadata.types.SensorDataContext]:
        """Get the next item to process. Returns `None` if no item is available.
        First, items from the manual queue with a priority > 0 are processed.
        Then, items from the storage directory are processed. Finally, items
        from the manual queue with a priority < 0 are processed."""

        self.iteration_count += 1

        next_manual_item = self._next_item_from_manual_queue()
        next_storage_item = (
            self._next_item_from_storage_directory()
            if self.config.automated_proffast.data_sources.storage
            else None
        )

        def process_scheduler_choice(
            choice: tum_esm_em27_metadata.types.SensorDataContext,
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
    ) -> Optional[tum_esm_em27_metadata.types.SensorDataContext]:
        """Use the dates from the storage directory"""
        max_date_string = min(
            (
                datetime.utcnow()
                - timedelta(
                    days=self.config.automated_proffast.storage_data_filter.min_days_delay
                )
            ).strftime("%Y%m%d"),
            self.config.automated_proffast.storage_data_filter.to_date,
        )
        date_strings = [
            str(d)
            for d in range(
                int(self.config.automated_proffast.storage_data_filter.from_date),
                int(max_date_string) + 1,
            )
            if (tum_esm_utils.text.is_date_string(str(d)))
        ][::-1]

        for date in date_strings:
            for (
                sensor_id
            ) in (
                self.config.automated_proffast.storage_data_filter.sensor_ids_to_consider
            ):
                if self._is_marked_as_processed(sensor_id, date):
                    continue

                # do not consider if outputs exist or out of filter range
                if self._outputs_exist(sensor_id, date):
                    self._mark_as_processed(sensor_id, date)
                    continue

                # skip this date right now it upload is incomplete
                # or date is too recent -> this might change during
                # the current execution, hence it will not be marked
                # as being processed
                if (not self._ifgs_exist(sensor_id, date)) or (
                    not self._upload_is_complete(sensor_id, date)
                ):
                    continue

                # do not consider if there is no location data
                try:
                    return self.em27_metadata.get(sensor_id=sensor_id, date=date)
                except AssertionError as a:
                    self.logger.debug(str(a))
                    self._mark_as_processed(sensor_id, date)
                    continue

        return None

    def _next_item_from_manual_queue(self) -> Optional[ManualQueueItem]:
        """use the dates from manual-queue.json"""
        next_items = interfaces.automated_proffast.ManualQueueInterface.get_items(
            self.logger
        )

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
            if (not self._ifgs_exist(next_item.sensor_id, next_item.date)) or (
                not self._upload_is_complete(next_item.sensor_id, next_item.date)
            ):
                continue

            # do not consider if there is no location data
            try:
                return ManualQueueItem(
                    sensor_data_context=self.em27_metadata.get(
                        sensor_id=next_item.sensor_id, date=next_item.date
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
        """for a given sensor_id and date, deter"""
        return os.path.isdir(
            os.path.join(
                self.config.general.data_src_dirs.interferograms,
                sensor_id,
                date,
            )
        )

    def _outputs_exist(self, sensor_id: str, date: str) -> bool:
        """for a given sensor_id and date, determine whether the
        outputs exist in the src directory"""
        successful_output_exists = os.path.isdir(
            os.path.join(
                self.config.general.data_dst_dirs.results,
                sensor_id,
                "proffast-2.2-outputs",
                "successful",
                date,
            )
        )
        failed_output_exists = os.path.isdir(
            os.path.join(
                self.config.general.data_dst_dirs.results,
                sensor_id,
                "proffast-2.2-outputs",
                "failed",
                date,
            )
        )
        return successful_output_exists or failed_output_exists

    def _upload_is_complete(self, sensor_id: str, date: str) -> bool:
        """
        If the dir_path contains a file "upload-meta.json", then this
        function returns whether the internally used format indicates
        a completed upload. Otherwise it will just return True
        """
        upload_meta_path = os.path.join(
            self.config.general.data_src_dirs.interferograms,
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
