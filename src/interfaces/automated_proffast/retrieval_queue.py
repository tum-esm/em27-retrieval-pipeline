import datetime
import json
import os
import re
from typing import Optional
import tum_esm_em27_metadata
from src import utils, custom_types


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

        self.iteration_index = 0
        self.verbose_reasoning = verbose_reasoning

        self.logger.debug("Precomputing queue items")
        self.queue_items: list[
            tum_esm_em27_metadata.types.SensorDataContext
        ] = self._get_storage_queue_items()

        self.logger.info("RetrievalQueue is set up")

    def get_next_item(self) -> Optional[tum_esm_em27_metadata.types.SensorDataContext]:
        """Get the next item to process. Returns `None` if no item is available."""

        # TODO: write remaining queue as json to logs directory

        if self.iteration_index > (len(self.queue_items) - 1):
            return None
        else:
            self.iteration_index += 1
            return self.queue_items[self.iteration_index - 1]

    def _get_storage_queue_items(
        self,
    ) -> list[tum_esm_em27_metadata.types.SensorDataContext]:
        assert self.config.automated_proffast is not None

        max_storage_date = min(
            datetime.datetime.utcnow().date()
            - datetime.timedelta(
                days=self.config.automated_proffast.data_filter.min_days_delay
            ),
            self.config.automated_proffast.data_filter.to_date,
        )

        storage_dates: list[datetime.date] = []
        current_date = self.config.automated_proffast.data_filter.from_date
        while current_date <= max_storage_date:
            storage_dates.append(current_date)
            current_date += datetime.timedelta(days=1)

        queue_items: list[tum_esm_em27_metadata.types.SensorDataContext] = []

        for date in storage_dates[::-1]:
            for (
                sensor_id
            ) in self.config.automated_proffast.data_filter.sensor_ids_to_consider:
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

                queue_items += sensor_data_contexts

        return queue_items

    def _ifgs_exist(self, sensor_id: str, date: datetime.date) -> bool:
        """determine whether an ifg directory exists and contains
        at least one interferogram"""

        assert self.config.automated_proffast is not None

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
