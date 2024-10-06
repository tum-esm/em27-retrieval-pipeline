from typing import Any, Optional
import datetime
import os
import em27_metadata
import tum_esm_utils
from src import types, utils, retrieval


# pprint outputs didn't look so great
def _list_to_pretty_string(l: list[Any]) -> str:
    if len(l) == 0:
        return "[]"
    string_items = [str(item) for item in l]
    out = "[\n    "
    current_indent = 4
    for item in string_items:
        if (current_indent + len(item)) > 80:
            out += "\n    "
            current_indent = 4
        out += item + ", "
        current_indent += len(item) + 2
    out += "\n]"
    return out


def generate_retrieval_queue(
    config: types.Config,
    logger: retrieval.utils.logger.Logger,
    em27_metadata_interface: em27_metadata.EM27MetadataInterface,
    retrieval_job_config: types.RetrievalJobConfig,
) -> list[em27_metadata.types.SensorDataContext]:
    assert config.retrieval is not None, "Config must have a retrieval section"

    def _log_filtering_step_message(
        positive_message: str,
        positive_items: set[datetime.date] | list[em27_metadata.types.SensorDataContext],
        negative_message: Optional[str] = None,
        negative_items: Optional[set[datetime.date] |
                                 list[em27_metadata.types.SensorDataContext]] = None,
    ) -> None:
        assert config.retrieval is not None
        pretty_items: list[str]
        message = f"    {len(positive_items)} {positive_message}"
        if config.retrieval.general.queue_verbosity == "verbose":
            pretty_items = []
            for item in positive_items:
                if isinstance(item, datetime.date):
                    pretty_items.append(item.strftime("%Y-%m-%d"))
                elif isinstance(item, em27_metadata.types.SensorDataContext):
                    pretty_items.append(
                        f"{item.from_datetime.strftime('%Y-%m-%dT%H:%M:%S')}-{item.to_datetime.strftime('%Y-%m-%dT%H:%M:%S')}-{item.location.location_id}"
                    )
                else:
                    pretty_items.append(item)
            message += ": " + _list_to_pretty_string(sorted(pretty_items))
            #pprint.pformat(pretty_items, compact=True, width=100, indent=4)[1 :]
        logger.info(message)

        if negative_message is None or negative_items is None:
            return

        message = f"    {len(negative_items)} {negative_message} (NOT PROCESSED)"
        if config.retrieval.general.queue_verbosity == "verbose":
            pretty_items = []
            for item in negative_items:
                if isinstance(item, datetime.date):
                    pretty_items.append(item.strftime("%Y-%m-%d"))
                elif isinstance(item, em27_metadata.types.SensorDataContext):
                    pretty_items.append(
                        f"{item.from_datetime.strftime('%Y-%m-%dT%H:%M:%S')}-{item.to_datetime.strftime('%Y-%m-%dT%H:%M:%S')}-{item.location.location_id}"
                    )
                else:
                    pretty_items.append(item)
            message += ": " + _list_to_pretty_string(sorted(pretty_items))
        logger.info(message)

    retrieval_queue: list[em27_metadata.types.SensorDataContext] = []
    for sensor in em27_metadata_interface.sensors.root:
        if sensor.sensor_id not in retrieval_job_config.sensor_ids:
            logger.info(f"Skipping sensor {sensor.sensor_id}")
            continue
        else:
            logger.info(f"Processing sensor {sensor.sensor_id}")

        # Find dates with location data

        logger.info("  Parsing metadata for location data")
        dates_with_location: set[datetime.date] = set()
        for sensor_setup in sensor.setups:
            overlap = tum_esm_utils.timing.datetime_span_intersection(
                (
                    sensor_setup.from_datetime,
                    sensor_setup.to_datetime,
                ),
                (
                    datetime.datetime.combine(
                        retrieval_job_config.from_date,
                        datetime.time.min,
                        tzinfo=datetime.timezone.utc,
                    ),
                    datetime.datetime.combine(
                        retrieval_job_config.to_date,
                        datetime.time.max,
                        tzinfo=datetime.timezone.utc,
                    )
                ),
            )
            if overlap is not None:
                dates_with_location.update(
                    tum_esm_utils.timing.date_range(overlap[0].date(), overlap[1].date())
                )

        _log_filtering_step_message(
            positive_message="dates with location data",
            positive_items=dates_with_location,
        )

        # Only keep dates with interferograms

        dates_with_interferograms: set[datetime.date] = set()
        dates_without_interferograms: set[datetime.date] = set()
        for date in dates_with_location:
            ifg_path = os.path.join(
                config.general.data.interferograms.root, sensor.sensor_id, date.strftime("%Y%m%d")
            )
            if os.path.isdir(ifg_path):
                dates_with_interferograms.add(date)
            else:
                dates_without_interferograms.add(date)
        _log_filtering_step_message(
            positive_message="of these dates have interferograms",
            positive_items=dates_with_interferograms,
            negative_message="of these dates have no interferograms",
            negative_items=dates_without_interferograms,
        )

        dates_with_unlocked_interferograms: set[datetime.date] = set()
        dates_with_locked_interferograms: set[datetime.date] = set()
        for date in dates_with_interferograms:
            ifg_path = os.path.join(
                config.general.data.interferograms.root, sensor.sensor_id, date.strftime("%Y%m%d")
            )
            assert os.path.isdir(ifg_path)
            do_not_touch_indicator_file = os.path.join(ifg_path, ".do-not-touch")
            if os.path.isfile(do_not_touch_indicator_file):
                dates_with_locked_interferograms.add(date)
            else:
                dates_with_unlocked_interferograms.add(date)
        _log_filtering_step_message(
            positive_message="of these dates have unlocked interferograms",
            positive_items=dates_with_unlocked_interferograms,
            negative_message="of these dates have locked interferograms",
            negative_items=dates_with_locked_interferograms,
        )

        # Get sensor data contexts for all dates with interferograms

        sensor_data_contexts: list[em27_metadata.types.SensorDataContext] = []
        for date in dates_with_unlocked_interferograms:
            from_datetime = datetime.datetime(
                date.year, date.month, date.day, 0, 0, 0, tzinfo=datetime.timezone.utc
            )
            to_datetime = datetime.datetime(
                date.year, date.month, date.day, 23, 59, 59, tzinfo=datetime.timezone.utc
            )
            sensor_data_contexts.extend(
                em27_metadata_interface.get(sensor.sensor_id, from_datetime, to_datetime)
            )
        _log_filtering_step_message(
            positive_message="sensor data contexts generated",
            positive_items=sensor_data_contexts,
        )

        # Filter out the sensor data contexts which have already been processed
        # i.e. there is a results directory for them

        unprocessed_sensor_data_contexts: list[em27_metadata.types.SensorDataContext] = []
        results_dir = os.path.join(
            config.general.data.results.root, retrieval_job_config.retrieval_algorithm,
            retrieval_job_config.atmospheric_profile_model, sensor.sensor_id
        )
        for sdc in sensor_data_contexts:
            output_folder = sdc.from_datetime.strftime("%Y%m%d")
            if not utils.functions.sdc_covers_the_full_day(sdc):
                output_folder += sdc.from_datetime.strftime("_%H%M%S")
                output_folder += sdc.to_datetime.strftime("_%H%M%S")
            if retrieval_job_config.settings.output_suffix is not None:
                output_folder += f"_{retrieval_job_config.settings.output_suffix}"
            success_dir = os.path.join(results_dir, "successful", output_folder)
            failure_dir = os.path.join(results_dir, "failed", output_folder)
            if (not os.path.isdir(success_dir) and not os.path.isdir(failure_dir)):
                unprocessed_sensor_data_contexts.append(sdc)
        _log_filtering_step_message(
            positive_message="of these sensor data contexts have not been processed yet",
            positive_items=unprocessed_sensor_data_contexts,
        )

        # Only keep the sensor data contexts with ground pressure files

        unprocessed_sensor_data_contexts_with_ground_pressure_files: list[
            em27_metadata.types.SensorDataContext] = []
        unprocessed_sensor_data_contexts_without_ground_pressure_files: list[
            em27_metadata.types.SensorDataContext] = []
        for sdc in unprocessed_sensor_data_contexts:
            pressure_file_exists = retrieval.utils.pressure_loading.pressure_files_exist(
                config.general.data.ground_pressure.path.root, sdc.pressure_data_source,
                config.general.data.ground_pressure.file_regex, sdc.from_datetime.date()
            )
            if pressure_file_exists:
                unprocessed_sensor_data_contexts_with_ground_pressure_files.append(sdc)
            else:
                unprocessed_sensor_data_contexts_without_ground_pressure_files.append(sdc)

        _log_filtering_step_message(
            positive_message="of these sensor data contexts have ground pressure files",
            positive_items=unprocessed_sensor_data_contexts_with_ground_pressure_files,
            negative_message="of these sensor data contexts have no ground pressure files",
            negative_items=unprocessed_sensor_data_contexts_without_ground_pressure_files,
        )

        # Only keep the sensor data contexts with atmospheric profiles

        unprocessed_sensor_data_contexts_with_atmospheric_profiles: list[
            em27_metadata.types.SensorDataContext] = []
        unprocessed_sensor_data_contexts_without_atmospheric_profiles: list[
            em27_metadata.types.SensorDataContext] = []
        for sdc in unprocessed_sensor_data_contexts_with_ground_pressure_files:
            profiles_dir = os.path.join(
                config.general.data.atmospheric_profiles.root,
                retrieval_job_config.atmospheric_profile_model
            )
            cd = utils.text.get_coordinates_slug(
                sdc.atmospheric_profile_location.lat, sdc.atmospheric_profile_location.lon
            )
            date_slugs = sdc.from_datetime.strftime("%Y%m%d")
            datetime_slugs: list[str]
            if retrieval_job_config.atmospheric_profile_model == "GGG2014":
                datetime_slugs = [date_slugs]
            else:
                datetime_slugs = [f"{date_slugs}{d:02}" for d in [0, 3, 6, 9, 12, 15, 18, 21]]

            # Using this logic instead of something like `all([... for ...])`
            # so that it stops looking on the first encountered missing file
            profiles_complete: bool = True
            for datetime_slug in datetime_slugs:
                if not os.path.isfile(os.path.join(profiles_dir, f"{datetime_slug}_{cd}.map")):
                    profiles_complete = False
                    break
            if profiles_complete:
                unprocessed_sensor_data_contexts_with_atmospheric_profiles.append(sdc)
        _log_filtering_step_message(
            positive_message="of these sensor data contexts have atmospheric profiles",
            positive_items=unprocessed_sensor_data_contexts_with_atmospheric_profiles,
            negative_message="of these sensor data contexts have no atmospheric profiles",
            negative_items=unprocessed_sensor_data_contexts_without_atmospheric_profiles,
        )

        # Append the files

        retrieval_queue.extend(unprocessed_sensor_data_contexts_with_atmospheric_profiles)

    return sorted(
        sorted(
            retrieval_queue,
            key=lambda sdc: sdc.sensor_id,
            reverse=False,
        ),
        key=lambda sdc: sdc.from_datetime,
        reverse=True
    )
