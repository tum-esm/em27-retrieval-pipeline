import json
from typing import Literal
import tum_esm_utils
import os, copy
from ftplib import FTP
from rich.progress import track
from src import custom_types, procedures, utils

PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=2)


def run() -> None:
    # Configuration
    with open(os.path.join(PROJECT_DIR, "config", "config.json"), "r") as f:
        config = custom_types.Config(**json.load(f))

    # Generate daily sensor sets
    daily_sensor_sets = procedures.vertical_profiles.get_daily_sensor_sets(config)
    if len(daily_sensor_sets.keys()) == 0:
        print("No data to request.")
        return

    with FTP(
        host="ccycle.gps.caltech.edu",
        passwd=config.vertical_profiles.ftp_server.email,
        user="anonymous",
        timeout=60,
    ) as ftp:

        versions: list[Literal["GGG2014", "GGG2020"]] = []
        if config.vertical_profiles.request_scope.ggg_2014_download:
            versions.append("GGG2014")
        if config.vertical_profiles.request_scope.ggg_2020_download:
            versions.append("GGG2020")

        # Request GGG2014 and/or GGG2020 data
        for version in versions:

            # Retain daily_sensor_sets for export
            sensor_sets = copy.deepcopy(daily_sensor_sets)

            # Filter out existing data
            sensor_sets = procedures.vertical_profiles.filter_daily_sensor_sets(
                sensor_sets, version
            )
            if not sensor_sets:
                continue

            # Combine sensor sets to query intervals
            query_list = procedures.vertical_profiles.get_query_list(sensor_sets)

            with utils.vertical_profiles.Reporter(query_list, version) as reporter:

                for query in track(query_list, description=f"Downloading {version}..."):
                    # Check if data already exists on FTP server
                    up_status, up_time = True, 0.0
                    (
                        down_status,
                        down_time,
                        to_date,
                    ) = procedures.vertical_profiles.download_data(
                        config, query, ftp, version
                    )
                    if not down_status:
                        # Request data
                        (
                            up_status,
                            up_time,
                        ) = procedures.vertical_profiles.upload_request(
                            config.vertical_profiles.ftp_server, query, ftp, version
                        )
                        if up_status:
                            # Await data if upload successful
                            (
                                down_status,
                                down_time,
                                to_date,
                            ) = procedures.vertical_profiles.download_data(
                                config, query, ftp, version, wait=True
                            )

                    # Append query statistics to report
                    reporter.report_query(
                        query,
                        up_status,
                        up_time,
                        down_status,
                        down_time,
                        to_date,
                    )

                    if not down_status:
                        return

                # Export data to dst_dir
                procedures.vertical_profiles.export_data(
                    config, daily_sensor_sets, version
                )
