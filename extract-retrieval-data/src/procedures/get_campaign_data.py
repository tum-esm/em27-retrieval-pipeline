import os
from typing import Any

import asyncio
import itertools

from src import custom_types, utils


def _trim_data(
    from_date: str, to_date: str, data: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """_summary_"""

    # Drop data out of date range
    data = list(itertools.dropwhile(lambda x: x["to_date"] < from_date, data))
    data = list(itertools.dropwhile(lambda x: x["from_date"] > to_date, reversed(data)))
    if data:
        # Adjust boundary dates
        if from_date > data[0]["from_date"]:
            data[0]["from_date"] = from_date
        if to_date < data[-1]["to_date"]:
            data[-1]["to_date"] = to_date
    return data


def get_campaign_data(
    request_config: custom_types.RequestConfiguration,
    location_data_config: custom_types.LocationDataConfiguration,
) -> tuple[
    custom_types.Campaign,
    dict[str, custom_types.Location],
    dict[str, custom_types.Sensor],
]:
    """_summary_"""

    # Request campaigns, locations and sensors
    urls = [
        os.path.join(location_data_config.git_data_dir, task)
        for task in ("campaigns.json", "locations.json", "sensors.json")
    ]
    campaign_response, location_response, sensor_response = [
        response.json()
        for response in asyncio.run(
            utils.async_get_git_urls(
                git_username=location_data_config.git_username,
                git_token=location_data_config.git_token,
                urls=urls,
            )
        )
    ]

    # Parse campaign
    if request_config.campaign_name not in campaign_response:
        raise ValueError(f'"{request_config.campaign_name}" not in campaigns.json')
    campaign = custom_types.Campaign(**campaign_response[request_config.campaign_name])

    # Parse locations
    locations: dict[str, custom_types.Location] = {}
    for campaign_station in campaign.stations:
        if campaign_station.default_location not in location_response:
            raise ValueError(f'"{campaign_station.default_location}" not in locations.json')
        locations[campaign_station.default_location] = custom_types.Location(
            **location_response[campaign_station.default_location]
        )

    # Parse sensors
    sensors: dict[str, custom_types.Sensor] = {}
    for campaign_station in campaign.stations:
        if campaign_station.sensor not in sensor_response:
            raise ValueError(f'"{campaign_station.sensor}" not in sensors.json')

        # Trim utc_offsets and sensor_locations dates
        sensor_data = sensor_response[campaign_station.sensor]
        utc_offsets = _trim_data(
            request_config.from_date, request_config.to_date, sensor_data["utc_offsets"]
        )
        sensor_locations = [
            sensor_location
            for sensor_location in _trim_data(
                request_config.from_date, request_config.to_date, sensor_data["locations"]
            )
            # Sensors must be at their default location
            if sensor_location["location"] == campaign_station.default_location
        ]

        if sensor_locations:
            sensors[campaign_station.sensor] = custom_types.Sensor(
                serial_number=sensor_data["serial_number"],
                utc_offsets=utc_offsets,
                locations=sensor_locations,
            )

    return campaign, locations, sensors
