import datetime
import json
import os
import re
from typing import Literal, Optional
from pydantic import BaseModel
import tum_esm_em27_metadata
from src import utils, custom_types, interfaces


class QueueItem(BaseModel):
    priority: int
    sensor_data_context: tum_esm_em27_metadata.types.SensorDataContext


class RetrievalQueue:
    """1. Takes all items from manual-queue.json with a priority > 0
    2. Takes all dates from the config.data_src_dirs.interferograms
    3. Takes all items from manual-queue.json with a priority < 0"""

    def __init__(
        self,
        config: custom_types.Config,
        logger: utils.automated_proffast.Logger,
        em27_metadata: Optional[
            tum_esm_em27_metadata.interfaces.EM27MetadataInterface
        ] = None,
        verbose_reasoning: bool = False,
    ) -> None:
        """Initialize the retrieval queue.

        This includes loading the location data from GitHub using the package
        `tum_esm_em27_metadata`. "verbose reasoning" means that the retrieval
        queue will log the reason why it skips a certain item."""

        self.logger = logger
        self.config = config
        assert self.config.automated_proffast is not None
        self.logger.info("Initializing RetrievalQueue")

        self.logger.debug("Fetching metadata from GitHub")
        self.em27_metadata: tum_esm_em27_metadata.interfaces.EM27MetadataInterface
        if em27_metadata is not None:
            self.em27_metadata = em27_metadata
        else:
            self.em27_metadata = tum_esm_em27_metadata.load_from_github(
                github_repository=self.config.general.location_data.github_repository,
                access_token=self.config.general.location_data.access_token,
            )

        self.processed_sensor_dates: dict[str, list[datetime.datetime]] = {}

        self.iteration_count = 0
        self.verbose_reasoning = verbose_reasoning

        self.storage_queue_items: list[QueueItem] = []
        if self.config.automated_proffast.data_sources.storage:
            self.logger.debug("Precomputing storage queue items")
            self.storage_queue_items = self._get_storage_queue_items()
        else:
            self.logger.debug(
                "Skipping precomputation of storage queue (storage not considered)"
            )

        self.logger.info("RetrievalQueue is set up")

    def get_next_item(self) -> Optional[tum_esm_em27_metadata.types.SensorDataContext]:
        """Get the next item to process. Returns `None` if no item is available.
        First, items from the manual queue with a priority > 0 are processed.
        Then, items from the storage directory are processed. Finally, items
        from the manual queue with a priority < 0 are processed."""

        self.iteration_count += 1
        assert self.config.automated_proffast is not None

        next_manual_item: Optional[QueueItem] = None
        if self.config.automated_proffast.data_sources.manual_queue:
            next_manual_item = self._next_item_from_manual_queue()

        next_storage_item: Optional[QueueItem] = None
        if self.config.automated_proffast.data_sources.storage:
            next_storage_item = self._next_item_from_storage_directory()

        def _output(
            choice: QueueItem, source_label: str
        ) -> tum_esm_em27_metadata.types.SensorDataContext:
            self.logger.info(
                f"Scheduler iteration {self.iteration_count} - using {source_label}"
            )
            self._mark_as_processed(
                choice.sensor_data_context.sensor_id,
                choice.sensor_data_context.date,
            )
            return choice.sensor_data_context

        if next_manual_item is not None:
            if next_manual_item.priority > 0:
                return _output(next_manual_item, "manual queue (high priority)")
            else:
                if next_storage_item is not None:
                    return _output(next_storage_item, "storage directory")
                else:
                    return _output(next_manual_item, "manual queue (low priority)")
        else:
            if next_storage_item is not None:
                return _output(next_storage_item, "storage directory")
            else:
                return None

    def _get_storage_queue_items(self) -> list[QueueItem]:
        assert self.config.automated_proffast is not None

        max_storage_date = min(
            datetime.datetime.utcnow().date()
            - datetime.timedelta(
                days=self.config.automated_proffast.storage_data_filter.min_days_delay
            ),
            self.config.automated_proffast.storage_data_filter.to_date,
        )

        storage_dates: list[datetime.date] = []
        current_date = self.config.automated_proffast.storage_data_filter.from_date
        while current_date <= max_storage_date:
            storage_dates.append(current_date)
            current_date += datetime.timedelta(days=1)

        queue_items: list[QueueItem] = []

        for date in storage_dates[::-1]:
            for (
                sensor_id
            ) in (
                self.config.automated_proffast.storage_data_filter.sensor_ids_to_consider
            ):
                if not self._ifgs_exist(sensor_id, date):
                    if self.verbose_reasoning:
                        self.logger.debug(
                            f"skipping {sensor_id}/{date} because ifgs do not exist"
                        )
                    continue
                if self._upload_is_incomplete(sensor_id, date):
                    if self.verbose_reasoning:
                        self.logger.debug(
                            f"skipping {sensor_id}/{date} because upload is incomplete"
                        )
                    continue

                try:
                    sensor_data_contexts = self.em27_metadata.get(
                        sensor_id=sensor_id,
                        from_datetime=datetime.datetime.combine(
                            date, datetime.time.min
                        ),
                        to_datetime=datetime.datetime.combine(date, datetime.time.max),
                    )
                except AssertionError as a:
                    self.logger.debug(str(a))
                    continue

                if len(sensor_data_contexts) == 0:
                    if self.verbose_reasoning:
                        self.logger.debug(
                            f"skipping {sensor_id}/{date} because no metadata exists"
                        )
                    continue

                try:
                    sensor_data_contexts = self._filter_existing_output_sdcs(
                        sensor_id, sensor_data_contexts
                    )
                except RuntimeError as e:
                    self.logger.debug(str(e))
                    continue

                if len(sensor_data_contexts) == 0:
                    if self.verbose_reasoning:
                        self.logger.debug(
                            f"skipping {sensor_id}/{date} because all outputs exist"
                        )
                    continue

                for sdc in sensor_data_contexts:
                    queue_items.append(QueueItem(priority=0, sensor_data_context=sdc))

        return queue_items

    def _next_item_from_storage_directory(self) -> Optional[QueueItem]:
        """use the dates from the storage directory"""

        for item in self.storage_queue_items:
            if not self._is_marked_as_processed(
                item.sensor_data_context.sensor_id,
                item.sensor_data_context.from_datetime,
            ):
                return item

        return None

    def _next_item_from_manual_queue(self) -> Optional[QueueItem]:
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

            if self._is_marked_as_processed(
                next_item.sensor_id, next_item.from_datetime
            ):
                continue

            # skip this date right now it upload is incomplete
            # -> this might change during the current execution,
            # hence it will not be marked as being processed
            if self._upload_is_incomplete(next_item.sensor_id, next_item.from_datetime):
                continue

            # do not consider if there is no location data
            try:
                return QueueItem(
                    sensor_data_context=self.em27_metadata.get(
                        sensor_id=next_item.sensor_id, date=next_item.date
                    ),
                    priority=next_item.priority,
                )
            except AssertionError as a:
                self.logger.debug(str(a))
                self._mark_as_processed(next_item.sensor_id, next_item.date)
                continue

    def _mark_as_processed(self, sensor_id: str, dt: datetime.datetime) -> None:
        try:
            self.processed_sensor_dates[sensor_id].append(dt)
        except KeyError:
            self.processed_sensor_dates[sensor_id] = [dt]

    def _is_marked_as_processed(self, sensor_id: str, dt: datetime.datetime) -> bool:
        if sensor_id in self.processed_sensor_dates.keys():
            return dt in self.processed_sensor_dates[sensor_id]
        return False

    def _ifgs_exist(self, sensor_id: str, date: datetime.date) -> bool:
        """determine whether an ifg directory exists and contains
        at least one interferogram"""

        ifg_src_directory = os.path.join(
            self.config.general.data_src_dirs.interferograms,
            sensor_id,
            date.strftime("%Y%m%d"),
        )
        if not os.path.isdir(ifg_src_directory):
            return False

        expected_ifg_regex = (
            self.config.automated_proffast.general.ifg_file_regex.replace(
                "$(SENSOR_ID)", sensor_id
            ).replace("$(DATE)", date.strftime("%Y%m%d"))
        )
        expected_ifg_pattern = re.compile(expected_ifg_regex)
        return (
            len(
                [
                    f
                    for f in os.listdir(ifg_src_directory)
                    if expected_ifg_pattern.match(f) is not None
                ]
            )
            > 0
        )

    def _filter_existing_output_sdcs(
        self,
        sensor_id: str,
        sensor_data_contexts: list[tum_esm_em27_metadata.types.SensorDataContext],
    ) -> list[tum_esm_em27_metadata.types.SensorDataContext]:
        """For a given list of sensor data context of one day, remove those
        that already have outputs."""

        if len(sensor_data_contexts) == 1:
            expected_output_dir_names = set(
                [sensor_data_contexts[0].from_datetime.strftime("%Y%m%d")]
            )
        else:
            expected_output_dir_names = set(
                [
                    (
                        sdc.from_datetime.strftime("%Y%m%d_%H:%M:%S")
                        + "_"
                        + sdc.to_datetime.strftime("%H:%M:%S")
                    )
                    for sdc in sensor_data_contexts
                ]
            )

        existing_output_dir_names: set[str] = set()
        for output_dir_type in ["successful", "failed"]:
            existing_output_dir_names = existing_output_dir_names.union(
                set(
                    utils.functions.list_directory(
                        os.path.join(
                            self.config.general.data_dst_dirs.results,
                            sensor_id,
                            "proffast-2.2-outputs",
                            output_dir_type,
                        ),
                        is_directory=True,
                        regex=(
                            r"^"
                            + sensor_data_contexts[0].from_datetime.strftime("%Y%m%d")
                            + r".*"
                        ),
                    )
                )
            )

        if len(existing_output_dir_names) == 0:
            return sensor_data_contexts

        if existing_output_dir_names == expected_output_dir_names:
            return []

        if existing_output_dir_names.issubset(expected_output_dir_names):
            return [
                sdc
                for sdc in sensor_data_contexts
                if (
                    (
                        sdc.from_datetime.strftime("%Y%m%d_%H:%M:%S")
                        + "_"
                        + sdc.to_datetime.strftime("%H:%M:%S")
                    )
                    not in existing_output_dir_names
                )
            ]

        # happens when the metadata time sections are
        # changed after a retrieval has been completed
        raise RuntimeError(
            "Existing output directories are not compatible with the current "
            + "metadata. This happens when the metadata time sections are "
            + "changed after a retrieval has been completed. Please remove the "
            + "following directories and try again: "
            + ", ".join(
                [
                    os.path.join(
                        self.config.general.data_dst_dirs.results,
                        sensor_id,
                        "proffast-2.2-outputs",
                        output_dir_type,
                        dir_name,
                    )
                    for dir_name in existing_output_dir_names
                ]
            )
        )

    def _upload_is_incomplete(self, sensor_id: str, date: datetime.date) -> bool:
        """
        If the dir_path contains a file "upload-meta.json", then this
        function returns whether the internally used format indicates
        a completed upload. Otherwise it will just return True
        """
        ifg_dir_path = os.path.join(
            self.config.general.data_src_dirs.interferograms,
            sensor_id,
            date.strftime("%Y%m%d"),
        )

        if os.path.isfile(os.path.join(ifg_dir_path, ".do-no-touch")):
            return True

        try:
            with open(os.path.join(ifg_dir_path, "upload-meta.json")) as f:
                return json.load(f)["complete"] == False  # type: ignore
        except:
            return False
