import datetime
import os
import em27_metadata
import tum_esm_utils
from src import types, utils, retrieval


def generate_retrieval_queue(
    config: types.Config, logger: retrieval.utils.logger.Logger,
    em27_metadata_interface: em27_metadata.EM27MetadataInterface,
    retrieval_job_config: types.RetrievalJobConfig
) -> list[em27_metadata.types.SensorDataContext]:
    retrieval_queue: list[em27_metadata.types.SensorDataContext] = []
    for sensor in em27_metadata_interface.sensors.root:
        if sensor.sensor_id not in retrieval_job_config.sensor_ids:
            logger.info(f"Skipping sensor {sensor.sensor_id}")
            continue
        else:
            logger.info(f"Processing sensor {sensor.sensor_id}")

        # Find dates with location data

        dates_with_location: set[datetime.date] = set()
        for sensor_setup in sensor.setups:
            if ((
                sensor_setup.to_datetime.date() < retrieval_job_config.from_date
            ) or (
                sensor_setup.from_datetime.date() > retrieval_job_config.to_date
            )):
                continue
            dates_with_location.update(
                tum_esm_utils.timing.date_range(
                    max(
                        sensor_setup.from_datetime.date(),
                        retrieval_job_config.from_date
                    ),
                    min(
                        sensor_setup.to_datetime.date(),
                        retrieval_job_config.to_date
                    )
                )
            )
        logger.info(
            f"  Found {len(dates_with_location)} dates with location data"
        )

        # Only keep dates with interferograms

        dates_with_interferograms: set[datetime.date] = set()
        dates_with_unlocked_interferograms: set[datetime.date] = set()
        for date in dates_with_location:
            ifg_path = os.path.join(
                config.general.data.interferograms.root, sensor.sensor_id,
                date.strftime("%Y%m%d")
            )
            if os.path.isdir(ifg_path):
                dates_with_interferograms.add(date)
                do_not_touch_indicator_file = os.path.join(
                    ifg_path, ".do-not-touch"
                )
                if not os.path.isfile(do_not_touch_indicator_file):
                    dates_with_unlocked_interferograms.add(date)
        logger.info(
            f"  {len(dates_with_interferograms)} of these " +
            "dates have interferograms"
        )
        logger.info(
            f"  {len(dates_with_unlocked_interferograms)} of these " +
            "dates have interferograms with no process lock"
        )

        # Get sensor data contexts for all dates with interferograms

        sensor_data_contexts: list[em27_metadata.types.SensorDataContext] = []
        for date in dates_with_unlocked_interferograms:
            from_datetime = datetime.datetime(
                date.year, date.month, date.day, 0, 0, 0, tzinfo=datetime.UTC
            )
            to_datetime = datetime.datetime(
                date.year,
                date.month,
                date.day,
                23,
                59,
                59,
                tzinfo=datetime.UTC
            )
            sensor_data_contexts.extend(
                em27_metadata_interface.get(
                    sensor.sensor_id, from_datetime, to_datetime
                )
            )
        logger.info(
            f"  Generated {len(sensor_data_contexts)} sensor data contexts for these dates"
        )

        # Filter out the sensor data contexts which have already been processed
        # i.e. there is a results directory for them

        unprocessed_sensor_data_contexts: list[
            em27_metadata.types.SensorDataContext] = []
        results_dir = os.path.join(
            config.general.data.results.root,
            retrieval_job_config.retrieval_algorithm,
            retrieval_job_config.atmospheric_profile_model, sensor.sensor_id
        )
        for sdc in sensor_data_contexts:
            output_folder = sdc.from_datetime.strftime("%Y%m%d")
            if not utils.functions.sdc_covers_the_full_day(sdc):
                output_folder += sdc.from_datetime.strftime("_%H%M%S")
                output_folder += sdc.to_datetime.strftime("_%H%M%S")
            success_dir = os.path.join(results_dir, "successful", output_folder)
            failure_dir = os.path.join(results_dir, "failed", output_folder)
            if (
                not os.path.isdir(success_dir) and
                not os.path.isdir(failure_dir)
            ):
                unprocessed_sensor_data_contexts.append(sdc)
        logger.info(
            f"  {len(unprocessed_sensor_data_contexts)} of these sensor data contexts "
            "have not been processed yet"
        )

        # Only keep the sensor data contexts with datalogger files

        unprocessed_sensor_data_contexts_with_datalogger_files: list[
            em27_metadata.types.SensorDataContext] = []
        for sdc in unprocessed_sensor_data_contexts:
            datalogger_file_path = os.path.join(
                config.general.data.datalogger.root,
                sdc.pressure_data_source,
                (
                    f"datalogger-{sdc.pressure_data_source}-" +
                    sdc.from_datetime.strftime("%Y%m%d") + ".csv"
                ),
            )
            if os.path.isfile(datalogger_file_path):
                unprocessed_sensor_data_contexts_with_datalogger_files.append(
                    sdc
                )
        logger.info(
            f"  {len(unprocessed_sensor_data_contexts_with_datalogger_files)} of these "
            "sensor data contexts have datalogger files"
        )

        # Only keep the sensor data contexts with atmospheric profiles

        unprocessed_sensor_data_contexts_with_atmospheric_profiles: list[
            em27_metadata.types.SensorDataContext] = []
        for sdc in unprocessed_sensor_data_contexts_with_datalogger_files:
            profiles_dir = os.path.join(
                config.general.data.atmospheric_profiles.root,
                retrieval_job_config.atmospheric_profile_model
            )
            cd = utils.text.get_coordinates_slug(
                sdc.atmospheric_profile_location.lat,
                sdc.atmospheric_profile_location.lon
            )
            date_slugs = sdc.from_datetime.strftime("%Y%m%d")
            datetime_slugs: list[str]
            if retrieval_job_config.atmospheric_profile_model == "GGG2014":
                datetime_slugs = [date_slugs]
            else:
                datetime_slugs = [
                    f"{date_slugs}{d:02}" for d in [0, 3, 6, 9, 12, 15, 18, 21]
                ]

            # Using this logic instead of something like `all([... for ...])`
            # so that it stops looking on the first encountered missing file
            profiles_complete: bool = True
            for datetime_slug in datetime_slugs:
                if not os.path.isfile(
                    os.path.join(profiles_dir, f"{datetime_slug}_{cd}.map")
                ):
                    profiles_complete = False
                    break
            if profiles_complete:
                unprocessed_sensor_data_contexts_with_atmospheric_profiles.append(
                    sdc
                )
        logger.info(
            f"  {len(unprocessed_sensor_data_contexts_with_atmospheric_profiles)} of these "
            "sensor data contexts have atmospheric profiles"
        )

        # Append the files

        retrieval_queue.extend(
            unprocessed_sensor_data_contexts_with_atmospheric_profiles
        )

    return sorted(
        sorted(
            retrieval_queue,
            key=lambda sdc: sdc.sensor_id,
            reverse=False,
        ),
        key=lambda sdc: sdc.from_datetime,
        reverse=True
    )
