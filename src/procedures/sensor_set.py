import os
from pathlib import Path
from collections import defaultdict
from distutils.dir_util import copy_tree
from datetime import timedelta
from src.custom_types import *

CACHE_PATH = os.path.join(Path(os.path.abspath(__file__)).parents[2], ".cache")


def get_daily_sensor_sets(
    config: RequestConfig, locations: dict[LocationId, Location], sensors: dict[SensorId, Sensor]
) -> dict[QueryLocation, dict[Date, set[SensorId]]]:

    """
    Returns a dictionary that maps query locations to sensor sets.
    Sensor sets map days to a all sensors ids that were located at
    the query location on that day. Note that query locations store
    rounded coordinates and thus might bundle multiple locations.
    """

    daily_sensor_sets: dict[QueryLocation, dict[Date, set[SensorId]]] = defaultdict(
        lambda: defaultdict(set)
    )

    for sensor_id, sensor in sensors.items():
        for sensor_location in sensor.locations:

            # Overlap dates with requested dates
            from_date = max(sensor_location.from_date, config.from_date)
            to_date = min(sensor_location.to_date, config.to_date)

            # Sensors must be in date range
            if from_date > to_date:
                continue

            # Extract location data
            if sensor_location.location not in locations:
                raise ValueError(f'"{sensor_location.location}" not in {locations}')
            location = locations[sensor_location.location]

            # Iterate over individual days and add sensor
            date, stop = str_to_dt(from_date), str_to_dt(to_date)
            query_location = QueryLocation(lat=round(location.lat), lon=round(location.lon))

            while date <= stop:
                daily_sensor_sets[query_location][dt_to_str(date)].add(sensor_id)
                date += timedelta(+1)

    # Sort the date keys within each sensor set
    return {location: dict(sorted(sets.items())) for location, sets in daily_sensor_sets.items()}


def filter_daily_sensor_sets(
    daily_sensor_sets: dict[QueryLocation, dict[Date, set[SensorId]]],
    version: Version,
) -> dict[QueryLocation, dict[Date, set[SensorId]]]:
    """
    Removes sensor sets from daily_sensor_sets for
    which an according directory exists in .cache/{version}.
    """

    cache_path = f"{CACHE_PATH}/{version}"

    filtered_daily_sensor_sets = {}
    for location, location_sensor_sets in daily_sensor_sets.items():

        filtered_location_sensor_sets = {
            date: sensors.copy()
            for date, sensors in location_sensor_sets.items()
            if not os.path.isdir(f"{cache_path}/{date}_{location.slug()}")
        }

        if filtered_location_sensor_sets:
            filtered_daily_sensor_sets[location] = filtered_location_sensor_sets

    return filtered_daily_sensor_sets


def export_data(
    config: RequestConfig,
    daily_sensor_sets: dict[QueryLocation, dict[Date, set[SensorId]]],
    version: Version,
) -> None:
    """
    Exports data from .cache/{version} to {config.dst_dir}/{version}.
    Creates a subdirectory for each sensor id in the daily_sensor_set.
    """

    cache_path = f"{CACHE_PATH}/{version}"
    dst_path = os.path.join(config.dst_dir, version)

    for location, location_sensor_sets in daily_sensor_sets.items():
        for date, sensors in location_sensor_sets.items():
            for sensor in sensors:
                dir_ = f"{date}_{location.slug()}"
                if os.path.isdir(f"{cache_path}/{dir_}"):
                    copy_tree(f"{cache_path}/{dir_}", f"{dst_path}/{sensor}/{dir_}")
