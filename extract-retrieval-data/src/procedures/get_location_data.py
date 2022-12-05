import os

import asyncio

from src import custom_types, utils


def get_location_data(
    location_data_config: custom_types.LocationDataConfiguration,
    campaign_keys: list[str] | None = None,
    location_keys: list[str] | None = None,
    sensor_keys: list[str] | None = None,
) -> tuple[
    dict[str, custom_types.Campaign],
    dict[str, custom_types.Location],
    dict[str, custom_types.Sensor],
]:
    """_summary_"""

    urls = [
        os.path.join(location_data_config.git_data_dir, file_)
        for file_ in ("campaigns.json", "locations.json", "sensors.json")
    ]

    campaign_response, location_response, sensor_response = asyncio.run(
        utils.async_get_git_urls(
            location_data_config.git_username, location_data_config.git_token, urls
        )
    )

    campaigns = {
        campaign_key: custom_types.Campaign(**data)
        for campaign_key, data in campaign_response.json().items()
        if campaign_keys is None or campaign_key in campaign_keys
    }

    locations = {
        location_key: custom_types.Location(**data)
        for location_key, data in location_response.json().items()
        if location_keys is None or location_key in location_keys
    }

    sensors = {
        sensor_key: custom_types.Sensor(**data)
        for sensor_key, data in sensor_response.json().items()
        if sensor_keys is None or sensor_key in sensor_keys
    }

    return campaigns, locations, sensors
