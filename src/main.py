import json
import pathlib
import os, copy
from ftplib import FTP
from rich.progress import track

from src import custom_types, procedures, utils


def run() -> None:

    project_path = pathlib.Path(os.path.abspath(__file__)).parents[1]

    # Configuration
    with open(os.path.join(project_path, "config.json"), "r") as f:
        config = custom_types.Config(**json.load(f))

    # Request sensor and location data
    locations = procedures.get_location_data(config.github)
    sensors = procedures.get_sensor_data(config.github)

    # Generate daily sensor sets
    daily_sensor_sets = procedures.get_daily_sensor_sets(config.request, locations, sensors)
    if not daily_sensor_sets:
        return

    with FTP(
        host="ccycle.gps.caltech.edu",
        passwd=config.ftp.email,
        user="anonymous",
        timeout=60,
    ) as ftp:

        # Request GGG2014 and/or GGG2020 data
        for version in config.request.versions:

            # Retain daily_sensor_sets for export
            sensor_sets = copy.deepcopy(daily_sensor_sets)

            # Filter out existing data
            sensor_sets = procedures.filter_daily_sensor_sets(sensor_sets, version)
            if not sensor_sets:
                continue

            # Combine sensor sets to query intervals
            query_list = procedures.get_query_list(sensor_sets)

            with utils.Reporter(query_list, version) as reporter:

                for query in track(query_list, description=f"Downloading {version}..."):
                    # Check if data already exists on FTP server
                    up_status, up_time = True, 0.0
                    down_status, down_time = procedures.download_data(
                        config.ftp, query, ftp, version
                    )
                    if not down_status:
                        # Request data
                        up_status, up_time = procedures.upload_request(
                            config.ftp, query, ftp, version
                        )
                        if up_status:
                            # Await data if upload successful
                            down_status, down_time = procedures.download_data(
                                config.ftp, query, ftp, version, wait=True
                            )

                    # Append query statistics to report
                    reporter.report_query(query, up_status, up_time, down_status, down_time)

                    if not down_status:
                        return

                # Export data to dst_dir
                procedures.export_data(config.request, daily_sensor_sets, version)
