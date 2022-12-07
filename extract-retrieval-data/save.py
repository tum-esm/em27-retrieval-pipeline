"""  # Parse campaign

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

    return campaign, locations, sensors """