import time
import io
import ftplib
import datetime
from src import types


def upload_request(
    config: types.Config,
    query: types.DownloadQuery,
    ftp: ftplib.FTP,
    atmospheric_profile_model: types.AtmosphericProfileModel,
) -> bool:
    """Requests Ginput data by uploading a '.txt' to 'ccycle.gps.caltech.edu'.
    Attempts until upload successful or config.upload_timeout is exceeded.
    Sleeps config.upload_sleep seconds in between each attempt. Returns
    whether successful and time.time() - upload_start."""

    assert config.profiles is not None, "this is a bug in the code"

    to_date: str
    if atmospheric_profile_model == "GGG2020":
        # Exclusive to date
        to_date = (query.to_date +
                   datetime.timedelta(days=1)).strftime("%Y%m%d")
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
        success = False
        upload_start = time.time()

        # TODO: use tenacity to retry a few times
        while (not success and time.time() - upload_start < 10):
            try:
                # Upload request
                ftp.storbinary(f"STOR upload/{filename}", file_)
                success = True
            except ftplib.error_perm as e:
                if str(e) == "553 Could not create file.":
                    # FTP server busy
                    time.sleep(10)
                else:
                    raise e

        return success
