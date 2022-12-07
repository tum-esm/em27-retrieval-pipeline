from typing import Any
import os

from datetime import datetime
from itertools import dropwhile
from asyncio import run as asyncio_run

from src import custom_types, utils, QueryList


def _trim_data(
    from_date: str, to_date: str, data: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """_summary_"""

    # Drop data out of date range
    data = list(dropwhile(lambda x: x["to_date"] < from_date, data))
    data = list(dropwhile(lambda x: x["from_date"] > to_date, reversed(data)))
    if data:
        # Adjust boundary dates (note: list reversed)
        data[-1]["from_date"] = max(data[-1]["from_date"], from_date)
        data[0]["to_date"] = min(data[0]["to_date"], to_date)
    return data


def build_query_list(
    request_config: custom_types.RequestConfiguration,
    location_data_config: custom_types.LocationDataConfiguration,
) -> tuple[QueryList, dict[custom_types.StationId, custom_types.StationInfo]]:
    """_summary_"""

    urls = [
        os.path.join(location_data_config.git_data_dir, task)
        for task in ("campaigns.json", "locations.json", "sensors.json")
    ]
    # Request campaigns, locations and sensors
    campaign_response, location_response, sensor_response = [
        response.json()
        for response in asyncio_run(
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
    campaign = campaign_response[request_config.campaign_name]

    # Overlap campaign dates and requested dates
    req_from_date = max(request_config.from_date, campaign["from_date"])
    req_to_date = min(request_config.to_date, campaign["to_date"])

    query_list = QueryList()
    stations: dict[custom_types.StationId, custom_types.StationInfo] = {}
    for station in campaign["stations"]:

        location_id = station["default_location"]
        if location_id not in location_response:
            raise ValueError(f'"{location_id}" not in locations.json')

        station_id = station["sensor"]
        if station_id not in sensor_response:
            raise ValueError(f'"{station_id}" not in sensors.json')

        # Join campaign with locations and sensors
        location_data = location_response[location_id]
        sensor_data = sensor_response[station_id]

        stations[station_id] = custom_types.StationInfo(
            sensor_serial_number=sensor_data["serial_number"],
            default_location=custom_types.Location(
                location_id=location_id,
                **location_data,
            ),
            direction=station["direction"],
        )

        # Build query list
        for location_data in _trim_data(req_from_date, req_to_date, sensor_data["locations"]):
            if location_data["location"] == location_id:
                # Sensors must be at default location
                query_list.insert(
                    from_date=datetime.strptime(location_data["from_date"], "%Y%m%d").date(),
                    to_date=datetime.strptime(location_data["to_date"], "%Y%m%d").date(),
                    sensor=station_id,
                )

    return query_list, stations
