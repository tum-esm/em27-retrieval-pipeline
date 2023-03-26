import os
from collections import defaultdict
from distutils.dir_util import copy_tree
from typing import Literal, Optional
import tum_esm_utils
import tum_esm_em27_metadata
from src import custom_types

PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=3)
CACHE_DIR = os.path.join(PROJECT_DIR, ".cache")


def get_daily_sensor_sets(
    config: custom_types.Config,
    em27_metadata: Optional[
        tum_esm_em27_metadata.interfaces.EM27MetadataInterface
    ] = None,
) -> dict[custom_types.DownloadQueryLocation, dict[str, set[str]]]:
    """
    Returns a dictionary that maps query locations to sensor sets.
    Sensor sets map days to a all sensors ids that were located at
    the query location on that day. Note that query locations store
    rounded coordinates and thus might bundle multiple locations.

    Example:

    ```python
    {
        QueryLocation(lat=48, lon=11): {
            "20200101": {"ma", "mb"},
            "20200102": {"ma", "mb"},
            "20200103": {"ma", "mb"},
        },
        QueryLocation(lat=48, lon=12): {
            "20200101": {"mc", "md"},
            "20200102": {"mc", "md"},
            "20200103": {"mc", "md"},
        },
    }
    ```
    """

    # Request sensor and location data
    if em27_metadata is None:
        em27_metadata = tum_esm_em27_metadata.load_from_github(
            github_repository=config.general.location_data.github_repository,
            access_token=config.general.location_data.access_token,
        )

    daily_sensor_sets: dict[
        custom_types.DownloadQueryLocation, dict[str, set[str]]
    ] = defaultdict(lambda: defaultdict(set))

    for sensor in em27_metadata.sensors:
        for sensor_location in sensor.locations:

            # do not consider sensor locations that are outside of the request scope
            if (
                sensor_location.to_date
                < config.vertical_profiles.request_scope.from_date
            ) or (
                sensor_location.from_date
                > config.vertical_profiles.request_scope.to_date
            ):
                continue

            # trim reqested dates to request scope
            from_date_string = max(
                sensor_location.from_date,
                config.vertical_profiles.request_scope.from_date,
            )
            to_date_string = min(
                sensor_location.to_date,
                config.vertical_profiles.request_scope.to_date,
            )

            # get location data
            location = next(
                l
                for l in em27_metadata.locations
                if l.location_id == sensor_location.location_id
            )
            query_location = custom_types.DownloadQueryLocation(
                lat=round(location.lat), lon=round(location.lon)
            )

            # Iterate over individual days and add sensor
            for date in range(int(from_date_string), int(to_date_string) + 1):
                if tum_esm_utils.text.is_date_string(str(date)):
                    daily_sensor_sets[query_location][str(date)].add(sensor.sensor_id)

    # Sort the date keys within each sensor set
    return {
        location: dict(sorted(sets.items()))
        for location, sets in daily_sensor_sets.items()
    }


def filter_daily_sensor_sets(
    daily_sensor_sets: dict[custom_types.DownloadQueryLocation, dict[str, set[str]]],
    version: Literal["GGG2014", "GGG2020"],
) -> dict[custom_types.DownloadQueryLocation, dict[str, set[str]]]:
    """
    Removes sensor sets from daily_sensor_sets for
    which an according directory exists in .cache/{version}.
    """

    filtered_daily_sensor_sets = {}
    for location, location_sensor_sets in daily_sensor_sets.items():

        filtered_location_sensor_sets = {
            date: sensors.copy()
            for date, sensors in location_sensor_sets.items()
            if not os.path.isdir(f"{CACHE_DIR}/{version}/{date}_{location.slug()}")
        }

        if filtered_location_sensor_sets:
            filtered_daily_sensor_sets[location] = filtered_location_sensor_sets

    return filtered_daily_sensor_sets


def export_data(
    config: custom_types.Config,
    daily_sensor_sets: dict[custom_types.DownloadQueryLocation, dict[str, set[str]]],
    version: Literal["GGG2014", "GGG2020"],
) -> None:
    """
    Exports data from .cache/{version} to {config.dst_dir}/{version}.
    Creates a subdirectory for each sensor id in the daily_sensor_set.
    """
    dst_path = os.path.join(config.vertical_profiles.request_scope.dst_dir, version)

    for location, location_sensor_sets in daily_sensor_sets.items():
        for date, sensors in location_sensor_sets.items():
            for sensor in sensors:
                dir_ = f"{date}_{location.slug()}"
                if os.path.isdir(f"{CACHE_DIR}/{version}/{dir_}"):
                    copy_tree(
                        f"{CACHE_DIR}/{version}/{dir_}",
                        f"{dst_path}/{sensor}/{dir_}",
                    )
