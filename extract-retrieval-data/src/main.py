import os
import json
import pathlib

from rich.progress import track

from src import custom_types, procedures


def run() -> None:

    # Configuration
    PROJECT_PATH = pathlib.Path(os.path.abspath(__file__)).parents[1]
    with open(os.path.join(PROJECT_PATH, "config.json"), "r") as f:
        config = custom_types.Config(**json.load(f))

    # Request campaign, sensor and location data
    campaigns = procedures.get_campaign_data(config.git)
    # locations = procedures.get_location_data(config.git)
    sensors = procedures.get_sensor_data(config.git)

    # Extract campaign
    campaign_name = config.request.campaign_name
    if campaign_name not in campaigns:
        raise ValueError(f'"{campaign_name}" not in campaigns.json')
    campaign = campaigns[campaign_name]

    # Generate daily sensor set
    daily_sensor_set = procedures.get_daily_sensor_set(config.request, campaign, sensors)

    if not config.request.override_data:
        # Filter out existing files
        daily_sensor_set = procedures.filter_daily_sensor_set(
            config.request, campaign_name, daily_sensor_set
        )

    # For each day, query database and produce .csv
    for date, sensor_set in track(daily_sensor_set.items(), description="Processing..."):

        sensor_dataframes = {}
        for sensor in sensor_set:

            # Request raw data for individual sensors
            sensor_dataframe = procedures.get_sensor_dataframe(config, date, sensor)
            if not sensor_dataframe.empty:

                # Post-process the raw dataframes
                sensor_dataframe = procedures.post_process_dataframe(
                    sensor_dataframe, config.request.sampling_rate
                )
                sensor_dataframes[sensor] = sensor_dataframe

        if sensor_dataframes:

            # Combine sensor_dataframes
            daily_dataframe = procedures.get_daily_dataframe(
                config.request, campaign, sensor_dataframes
            )
            # Get metadata str
            metadata = procedures.get_metadata()

            filename = os.path.join(
                config.request.dst_dir, f"{campaign_name}_em27_export_{date}.csv"
            )
            # Store data as .csv
            with open(filename, "w") as f:
                # Write metadata
                f.write(metadata)
                # Append data
                daily_dataframe.to_csv(f, na_rep="NaN", mode="a")
