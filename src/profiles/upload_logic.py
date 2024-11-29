import time
import io
import ftplib
import datetime
import rich.progress
from src import types, profiles


def upload_requests(
    config: types.Config,
    queries: list[types.DownloadQuery],
    ftp: ftplib.FTP,
    atmospheric_profile_model: types.AtmosphericProfileModel,
) -> None:
    """Requests Ginput data by uploading a '.txt' to 'ccycle.gps.caltech.edu'.
    Attempts until upload successful or config.upload_timeout is exceeded.
    Sleeps config.upload_sleep seconds in between each attempt. Returns
    whether successful and time.time() - upload_start."""

    assert config.profiles is not None, "this is a bug in the code"

    cache = profiles.cache.DownloadQueryCache.load()

    with rich.progress.Progress() as progress:
        for query in progress.track(queries, description="Requesting ..."):
            progress.print(f"Requesting {query}")

            t1 = time.time()

            to_date: str
            if atmospheric_profile_model == "GGG2020":
                # Exclusive to date
                to_date = (query.to_date + datetime.timedelta(days=1)).strftime("%Y%m%d")
                filename = "input_file_2020.txt"
            else:
                # Inclusive to date
                to_date = query.to_date_str
                filename = "input_file.txt"

            # Build request in-memory
            with io.BytesIO(
                "\n".join((
                    "mu",
                    query.from_date_str,
                    to_date,
                    str(query.lat),
                    str(query.lon),
                    config.profiles.server.email,
                )).encode("utf-8")
            ) as file_:
                upload_start_time = time.time()

                while (time.time() - upload_start_time) < 15:
                    try:
                        ftp.storbinary(f"STOR upload/{filename}", file_)
                        progress.print("Success")
                        break
                    except ftplib.error_perm as e:
                        if str(e) == "553 Could not create file.":
                            progress.print("Failed because FTP server is busy")
                            time.sleep(5)
                        else:
                            raise e

            cache.add_query(atmospheric_profile_model, query)
            cache.dump()
            print("Updated cache")

            if query == queries[-1]:
                print("All queries uploaded")
            else:
                t2 = time.time()

                # sleeping 65 seconds because these files are parsed by a cron
                # job every minute, so we need to wait for the cron job to
                # finish before we can upload the next request
                request_time = (t2 - t1)
                sleep_time = max(round(65 - request_time, 3), 0)
                if sleep_time > 0:
                    progress.print(f"Sleeping for {sleep_time} seconds")
                    time.sleep(sleep_time)
