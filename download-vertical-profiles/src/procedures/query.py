from typing import BinaryIO
import os
import time
import tarfile
from pathlib import Path
from io import BytesIO
from ftplib import FTP, error_perm
from datetime import datetime, timedelta
from src.custom_types import *

CACHE_PATH = os.path.join(Path(os.path.abspath(__file__)).parents[2], ".cache")


def get_query_list(
    daily_sensor_sets: dict[QueryLocation, dict[Date, set[SensorId]]]
) -> list[Query]:
    """
    Converts (ordered) daily_sensor_sets to a single query list.
    Queries cover mutually exclusive date ranges (less than 32 days)
    for one location and hereby administer future FTP requests.
    """
    query_list = []
    for location, location_sensor_sets in daily_sensor_sets.items():

        # Retrieve first date in location_sensor_sets
        date_iterator = iter(location_sensor_sets)
        from_date = str_to_dt(next(date_iterator))
        to_date = from_date
        days = 1

        # Iterate over remaining dates
        for date in date_iterator:
            next_day = to_date + timedelta(1)
            # If dates are not consecutive or job is longer than 31 days ...
            if (dt := str_to_dt(date)) != next_day or days > 31:
                # ... append accumulated interval and reset
                query_list.append(
                    Query(
                        from_date=dt_to_str(from_date),
                        to_date=dt_to_str(to_date),
                        location=location,
                    )
                )
                from_date = dt
                to_date = dt
                days = 1
            else:
                to_date = next_day
                days += 1

        # Append remaining interval
        query_list.append(
            Query(
                from_date=dt_to_str(from_date),
                to_date=dt_to_str(to_date),
                location=location,
            )
        )

    return query_list


def upload_request(
    config: FTPConfig, query: Query, ftp: FTP, version: Version
) -> tuple[bool, float]:
    """
    Requests Ginput data by uploading a '.txt' to 'ccycle.gps.caltech.edu'.
    Attempts until upload successful or config.upload_timeout is exceeded.
    Sleeps config.upload_sleep seconds in between each attempt.
    Returns whether successful and time.time() - upload_start.
    """
    if version == "GGG2020":
        # Exclusive to date
        to_date = dt_to_str(str_to_dt(query.to_date) + timedelta(1))
        filename = "input_file_2020.txt"
    else:
        # Inclusive to date
        to_date = query.to_date
        filename = "input_file.txt"

    # Build request in-memory
    with BytesIO(
        "\n".join(
            (
                "tu",
                query.from_date,
                to_date,
                str(query.location.lat),
                str(query.location.lon),
                config.email,
            )
        ).encode("utf-8")
    ) as file_:
        success = False
        upload_start = time.time()
        while not success and time.time() - upload_start < config.upload_timeout:
            try:
                # Upload request
                ftp.storbinary(f"STOR upload/{filename}", file_)
                success = True
            except error_perm as e:
                if str(e) == "553 Could not create file.":
                    # FTP server busy
                    time.sleep(config.upload_sleep)
                else:
                    raise e

        return success, time.time() - upload_start


def download_data(
    config: FTPConfig, query: Query, ftp: FTP, version: Version, wait: bool = False
) -> tuple[bool, float, str | None]:
    """
    Downloads .map, .mod and .vmr data and stores it in .cache/{version}.

    Searches exclusively for archive suffixes on the FTP server, given that
    job identifiers are unknown and sensor prefixes are irrelevant. Set 'wait'
    to True to attempt until the is found or config.download_timeout is
    exceeded. Sleeps config.download_sleep seconds in between each attempt.
    Returns whether successful, time.time() - upload_start and retrieved
    to date (as the server might truncate too recent requests).
    """

    response: set[str] = set()
    date_suffixes = _get_date_suffixes(config, query, version)

    if version == "GGG2020":
        remote_dirs = {"ginput-jobs"}
        suffixes = [f"{query.location.slug(verbose=True)}_{d}.tgz" for d in date_suffixes]
    else:
        remote_dirs = {"upload/modfiles/tar/maps", "upload/modfiles/tar/mods"}
        suffixes = [f"{query.location.slug()}_{d}.tar" for d in date_suffixes]

    to_date = None
    download_start = time.time()
    while response != remote_dirs and time.time() - download_start < config.download_timeout:

        if wait:
            time.sleep(config.download_sleep)

        for remote_dir in remote_dirs - response:
            nlst = ftp.nlst(remote_dir)
            # Retrieve archive with largest date range
            suffix, archive_str = next(
                (
                    (suffix, archive_str)
                    for suffix in suffixes
                    for archive_str in nlst
                    if archive_str.endswith(suffix)
                ),
                (None, None),
            )

            if suffix is not None:
                # Retrieve data in-memory
                with BytesIO() as archive:
                    ftp.retrbinary(
                        f"RETR {archive_str}",
                        archive.write,
                    )
                    archive.seek(0)
                    response.add(remote_dir)
                    to_date = suffix[-12:-4]
                    _extract_archive(archive, query, version)

        if not wait:
            break

    return response == remote_dirs, time.time() - download_start, to_date


def _get_date_suffixes(config: FTPConfig, query: Query, version: Version) -> list[str]:
    """
    Generates date range suffixes up to config.max_day_delay days before utcnow().
    """
    sep = "_"
    from_date = str_to_dt(query.from_date)
    to_date = str_to_dt(query.to_date)
    max_delay = max(from_date, (datetime.utcnow() - timedelta(days=config.max_day_delay)))

    if version == "GGG2020":
        # Exclusive to date
        to_date += timedelta(1)
        max_delay += timedelta(1)
        sep = "-"

    # Default query
    date_strs = [f"{query.from_date}{sep}{dt_to_str(to_date)}"]

    # Query archives up to config.max_delay days before utcnow()
    while to_date > max_delay:
        to_date -= timedelta(1)
        date_strs.append(f"{query.from_date}{sep}{dt_to_str(to_date)}")
    return date_strs


def _extract_archive(archive: BinaryIO, query: Query, version: Version) -> None:
    """
    Extracts, renames and stores archive members in .cache/{version}.
    """
    cache_path = f"{CACHE_PATH}/{version}"
    with tarfile.open(fileobj=archive) as tar:
        for member in tar:
            name = member.name

            if not name.endswith((".map", ".mod", ".vmr")):
                # Skip (sub-)directories
                continue

            if version == "GGG2020":
                if name.endswith(".map"):
                    date, hour, type_ = name[47:55], name[55:57], "map"
                elif name.endswith(".mod"):
                    date, hour, type_ = name[35:43], name[43:45], "mod"
                elif name.endswith(".vmr"):
                    date, hour, type_ = name[39:47], name[47:49], "vmr"
                member.name = f"{date}{hour}_{query.location.slug()}.{type_}"

            else:
                if name.endswith(".map"):
                    date, type_ = name[2:10], "map"
                elif name.endswith(".mod"):
                    date, type_ = name[5:13], "mod"
                member.name = f"{date}_{query.location.slug()}.{type_}"

            tar.extract(member, f"{cache_path}/{date}_{query.location.slug()}")
