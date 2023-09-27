import sys
import tum_esm_utils
from ftplib import FTP
from rich.progress import Progress

_PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(
    __file__, current_depth=2
)
sys.path.append(_PROJECT_DIR)

from src import custom_types, procedures, utils


def run() -> None:
    config = custom_types.Config.load()
    assert config.profiles is not None, "No profiles config found"

    try:

        for version in config.profiles.request_scope.data_types:
            print(f"Downloading {version} data")

            # Generate daily sensor sets
            download_queries = procedures.profiles.generate_download_queries(
                config, version
            )
            if len(download_queries) == 0:
                print("No data to request.")
                continue

            with FTP(
                host="ccycle.gps.caltech.edu",
                passwd=config.profiles.ftp_server.email,
                user="anonymous",
                timeout=60,
            ) as ftp:
                print(f"Running {len(download_queries)} queries: ")
                for query in download_queries:
                    print(f"    {query}")

                with utils.profiles.Reporter(
                    download_queries, version
                ) as reporter:
                    with Progress() as progress:
                        for query in progress.track(
                            list(
                                sorted(
                                    download_queries,
                                    key=lambda q: q.to_date,
                                    reverse=True
                                )
                            ),
                            description=f"Downloading ...",
                        ):
                            progress.print(
                                f"Downloading data for {query.lat}°N, {query.lon}°E,"
                                + f" {query.from_date} - {query.to_date}"
                            )

                            # Check if data already exists on FTP server
                            up_status, up_time = True, 0.0
                            (
                                down_status,
                                down_time,
                                to_date,
                            ) = procedures.profiles.download_data(
                                config, query, ftp, version
                            )
                            if not down_status:
                                # Request data
                                (
                                    up_status,
                                    up_time,
                                ) = procedures.profiles.upload_request(
                                    config, query, ftp, version
                                )
                                if up_status:
                                    # Await data if upload successful
                                    (
                                        down_status,
                                        down_time,
                                        to_date,
                                    ) = procedures.profiles.download_data(
                                        config, query, ftp, version, wait=True
                                    )

                            # Append query statistics to report
                            """reporter.report_query(
                                query,
                                up_status,
                                up_time,
                                down_status,
                                down_time,
                                to_date,
                            )"""

                            if not down_status:
                                return

                            progress.print(f"Done")
    except KeyboardInterrupt:
        print("Interrupted by user.")
        exit(1)


if __name__ == "__main__":
    run()
