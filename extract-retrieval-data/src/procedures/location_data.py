import os
import json
from src import utils

from src.custom_types import (
    GitHubConfig,
    CampaignId,
    LocationId,
    SensorId,
    Campaign,
    Location,
    Sensor,
)


def get_campaign_data(
    config: GitHubConfig,
) -> dict[CampaignId, Campaign]:
    """
    Requests campaigns.json from GitHub.
    Returns a dictionary that maps a campaign_id to its campaign.
    """
    url = os.path.join(config.data_dir, "campaigns.json")
    response = utils.network.request_url(url, config.username, config.token)
    return {campaign_id: Campaign(**data) for campaign_id, data in json.loads(response).items()}


def get_location_data(config: GitHubConfig) -> dict[LocationId, Location]:
    """
    Requests locations.json from GitHub.
    Returns a dictionary that maps a location_id to its location.
    """
    url = os.path.join(config.data_dir, "locations.json")
    response = utils.network.request_url(url, config.username, config.token)
    return {location_id: Location(**data) for location_id, data in json.loads(response).items()}


def get_sensor_data(config: GitHubConfig) -> dict[SensorId, Sensor]:
    """
    Requests sensors.json from GitHub.
    Returns a dictionary that maps a sensors_id to its sensor.
    """
    url = os.path.join(config.data_dir, "sensors.json")
    response = utils.network.request_url(url, config.username, config.token)
    return {sensor_id: Sensor(**data) for sensor_id, data in json.loads(response).items()}
