import sys
import tum_esm_utils
import copy
from ftplib import FTP
from rich.progress import Progress

_PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=2)
sys.path.append(_PROJECT_DIR)

from src import procedures, utils


def run() -> None:
    config = utils.load_config()

    # Generate daily sensor sets
    daily_sensor_sets = procedures.vertical_profiles.get_daily_sensor_sets(config)
    if len(daily_sensor_sets.keys()) == 0:
        print("No data to request.")
        return

    print("Export existing data")
    procedures.vertical_profiles.export_data(config, daily_sensor_sets, "GGG2014")

    with FTP(
        host="ccycle.gps.caltech.edu",
        passwd=config.vertical_profiles.ftp_server.email,
        user="anonymous",
        timeout=60,
    ) as ftp:
        # Request GGG2014 and/or GGG2020 data
        for version in config.vertical_profiles.request_scope.data_types:
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
            print(f"Running {len(query_list)} queries for {version}")

            with utils.vertical_profiles.Reporter(query_list, version) as reporter:
                with Progress() as progress:
                    for query in progress.track(
                        list(sorted(query_list, key=lambda q: q.to_date, reverse=True)),
                        description=f"Downloading {version}...",
                    ):
                        progress.print(
                            f"Downloading data for {query.location.lat}°N, {query.location.lon}°E,"
                            + f" {query.from_date} - {query.to_date}"
                        )

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

                        progress.print(f"Exporting")

                        # Export data to dst_dir
                        procedures.vertical_profiles.export_data(
                            config, daily_sensor_sets, version
                        )


if __name__ == "__main__":
    run()
