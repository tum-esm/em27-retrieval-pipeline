import os
from collections import defaultdict
from datetime import datetime, timedelta
from src.custom_types import (
    RequestConfig,
    CampaignId,
    SensorId,
    Campaign,
    Sensor,
    Date,
)


def get_daily_sensor_sets(
    config: RequestConfig, campaign: Campaign, sensors: dict[SensorId, Sensor]
) -> dict[Date, set[SensorId]]:
    """
    Returns a dictionary that maps days to a set of sensors ids.
    The set consists of all sensor ids that were located at their
    default location (defined for each campaign) on that day.
    """

    daily_sensor_sets = defaultdict(set)

    # Overlap campaign dates with requested dates
    req_from_date = max(config.from_date, campaign.from_date)
    req_to_date = min(config.to_date, campaign.to_date)

    for station in campaign.stations:
        sensor = sensors[station.sensor]
        for sensor_location in sensor.locations:

            # Overlap dates with from_date and to_date
            from_date = max(req_from_date, sensor_location.from_date)
            to_date = min(req_to_date, sensor_location.to_date)

            # Sensors must be in date range and at default location
            if from_date > to_date or sensor_location.location != station.default_location:
                continue

            # Iterate over individual days and add sensor
            date = datetime.strptime(from_date, "%Y%m%d").date()
            stop = datetime.strptime(to_date, "%Y%m%d").date()

            while date <= stop:
                daily_sensor_sets[date.strftime("%Y%m%d")].add(station.sensor)
                date += timedelta(+1)

    return daily_sensor_sets


def filter_daily_sensor_sets(
    config: RequestConfig, campaign_name: CampaignId, daily_sensor_sets: dict[Date, set[SensorId]]
) -> dict[Date, set[SensorId]]:
    """
    Removes sensor sets from daily_sensor_sets for
    which an according file exists in the dst_dir.
    """

    return {
        date: sensors.copy()
        for date, sensors in daily_sensor_sets.items()
        if not os.path.isfile(
            os.path.join(config.dst_dir, f"{campaign_name}_em27_export_{date}.csv")
        )
    }
