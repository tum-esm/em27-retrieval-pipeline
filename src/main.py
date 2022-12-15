import json
import pathlib
import os, copy
from ftplib import FTP
from rich.progress import track
from datetime import datetime

from src import custom_types, procedures


def run() -> None:

    project_path = pathlib.Path(os.path.abspath(__file__)).parents[1]

    # Prepare report summary
    report_name = datetime.utcnow().strftime("%Y%m%d%H%M")
    with open(f"{project_path}/ftp-reports/{report_name}.json", "w+") as report:
        json.dump({"queries": []}, report)

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

            for query in track(query_list, description=f"Downloading {version}..."):
                # Check if data already exists on FTP server
                up_status, up_time = True, -1.0
                down_status, down_time = procedures.download_data(config.ftp, query, ftp, version)
                if not down_status:
                    # Request data and download_data
                    up_status, up_time = procedures.upload_request(config.ftp, query, ftp, version)
                    down_status, down_time = procedures.download_data(
                        config.ftp, query, ftp, version, wait=True
                    )

                # Append query statistics to report summary
                with open(f"{project_path}/ftp-reports/{report_name}.json", "r+") as report:
                    data = json.load(report)
                    data["queries"].append(
                        query.to_json()
                        | {
                            "up_status": up_status,
                            "up_time": round(up_time),
                            "down_status": down_status,
                            "down_time": round(down_time),
                        }
                    )
                    report.seek(0)
                    json.dump(data, report, indent=4)

            # Export data to dst_dir
            procedures.export_data(config.request, daily_sensor_sets, version)
