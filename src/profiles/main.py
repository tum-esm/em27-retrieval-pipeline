import sys
import time
import tum_esm_utils
import ftplib
import rich.progress

sys.path.append(tum_esm_utils.files.rel_to_abs_path("../.."))
from src import types, profiles


def run() -> None:
    config = types.Config.load()
    assert config.profiles is not None, "No profiles config found"

    try:

        for version in config.profiles.scope.models:
            print(f"Downloading {version} data")

            # Generate daily sensor sets
            download_queries = profiles.generate_queries.generate_download_queries(
                config, version
            )
            if len(download_queries) == 0:
                print("No data to request.")
                continue

            with ftplib.FTP(
                host="ccycle.gps.caltech.edu",
                passwd=config.profiles.server.email,
                user="anonymous",
                timeout=60,
            ) as ftp:
                print(f"Running {len(download_queries)} queries: ")
                for query in download_queries:
                    print(f"    {query}")

                with rich.progress.Progress() as progress:
                    for query_index, query in progress.track(
                        enumerate(
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
                        t1 = time.time()

                        # Check if data already exists on FTP server
                        data_is_already_present = profiles.transfer_logic.download_data(
                            config, query, ftp, version
                        )
                        if data_is_already_present:
                            progress.print(
                                f"Data already present on FTP server"
                            )
                        else:
                            progress.print(f"Data not present on FTP server")

                            # TODO: skip if already requested in the last 48 hours

                            request_upload_successful = profiles.transfer_logic.upload_request(
                                config, query, ftp, version
                            )
                            if request_upload_successful:
                                progress.print(f"Request upload successful")
                                # TODO: store saved requests in a file
                            else:
                                progress.print(f"Request upload failed")

                            if query_index < len(download_queries) - 1:
                                t2 = time.time()
                                remaining_time = 65 - (t2 - t1)
                                if remaining_time > 0:
                                    progress.print(
                                        f"Waiting {remaining_time:.1f} seconds"
                                    )
                                    time.sleep(remaining_time)

                        progress.print(f"Done")
    except KeyboardInterrupt:
        print("Interrupted by user.")
        exit(1)


if __name__ == "__main__":
    run()
