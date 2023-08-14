from typing import BinaryIO, Callable, Literal, Optional
import time
import tarfile
from io import BytesIO
from ftplib import FTP, error_perm
import datetime
from src import custom_types, utils


def upload_request(
    config: custom_types.Config,
    query: custom_types.DownloadQuery,
    ftp: FTP,
    version: Literal["GGG2014", "GGG2020"],
) -> tuple[bool, float]:
    """Requests Ginput data by uploading a '.txt' to 'ccycle.gps.caltech.edu'.
    Attempts until upload successful or config.upload_timeout is exceeded.
    Sleeps config.upload_sleep seconds in between each attempt. Returns
    whether successful and time.time() - upload_start."""

    assert config.vertical_profiles is not None, "this is a bug in the code"

    to_date: str
    if version == "GGG2020":
        # Exclusive to date
        to_date = (query.to_date + datetime.timedelta(days=1)).strftime("%Y%m%d")
        filename = "input_file_2020.txt"
    else:
        # Inclusive to date
        to_date = query.to_date_string()
        filename = "input_file.txt"

    # Build request in-memory
    with BytesIO(
        "\n".join(
            (
                "tu",
                query.from_date_string(),
                to_date,
                str(query.lat),
                str(query.lon),
                config.vertical_profiles.ftp_server.email,
            )
        ).encode("utf-8")
    ) as file_:
        success = False
        upload_start = time.time()
        while (
            not success
            and time.time() - upload_start
            < config.vertical_profiles.ftp_server.upload_timeout
        ):
            try:
                # Upload request
                ftp.storbinary(f"STOR upload/{filename}", file_)
                success = True
            except error_perm as e:
                if str(e) == "553 Could not create file.":
                    # FTP server busy
                    time.sleep(config.vertical_profiles.ftp_server.upload_sleep)
                else:
                    raise e

        return success, time.time() - upload_start


def get_date_suffixes(
    config: custom_types.Config,
    query: custom_types.DownloadQuery,
    version: Literal["GGG2014", "GGG2020"],
    get_current_datetime: Callable[
        [], datetime.datetime
    ] = lambda: datetime.datetime.utcnow(),
) -> list[str]:
    """Generates date range suffixes up to config.max_day_delay
    days before utcnow()."""

    assert config.vertical_profiles is not None, "this is a bug in the code"

    sep = "_"
    worst_to_date = max(
        query.from_date,
        (
            get_current_datetime()
            - datetime.timedelta(
                days=config.vertical_profiles.ftp_server.max_day_delay + 1
            )
        ).date(),
    )
    best_to_date = query.to_date

    if version == "GGG2020":
        # Exclusive to date
        best_to_date += datetime.timedelta(days=1)
        worst_to_date += datetime.timedelta(days=1)
        sep = "-"

    # Default query
    date_strs = [
        f"{query.from_date.strftime('%Y%m%d')}{sep}{best_to_date.strftime('%Y%m%d')}"
    ]

    # Query archives up to config.max_delay days before utcnow()
    while best_to_date > worst_to_date:
        best_to_date -= datetime.timedelta(days=1)
        date_strs.append(
            f"{query.from_date.strftime('%Y%m%d')}{sep}{best_to_date.strftime('%Y%m%d')}"
        )
    return date_strs


def download_data(
    config: custom_types.Config,
    query: custom_types.DownloadQuery,
    ftp: FTP,
    version: Literal["GGG2014", "GGG2020"],
    wait: bool = False,
) -> tuple[bool, float, Optional[datetime.date]]:
    """Downloads .map, .mod and .vmr data.

    Searches exclusively for archive suffixes on the FTP server, given that
    job identifiers are unknown and sensor prefixes are irrelevant. Set 'wait'
    to True to attempt until the is found or config.download_timeout is
    exceeded. Sleeps config.download_sleep seconds in between each attempt.
    Returns whether successful, time.time() - upload_start and retrieved
    to date (as the server might truncate too recent requests).
    """

    assert config.vertical_profiles is not None, "this is a bug in the code"

    response: set[str] = set()
    date_suffixes = get_date_suffixes(config, query, version)

    if version == "GGG2020":
        remote_dirs = {"ginput-jobs"}
        suffixes = [
            f"{query.to_coordinates_slug(verbose=True)}_{d}.tgz" for d in date_suffixes
        ]
    else:
        remote_dirs = {"upload/modfiles/tar/maps", "upload/modfiles/tar/mods"}
        suffixes = [f"{query.to_coordinates_slug()}_{d}.tar" for d in date_suffixes]

    to_date: Optional[datetime.date] = None
    download_start = time.time()
    while (
        response != remote_dirs
        and time.time() - download_start
        < config.vertical_profiles.ftp_server.download_timeout
    ):
        if wait:
            time.sleep(config.vertical_profiles.ftp_server.download_sleep)

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
                    to_date = datetime.datetime.strptime(
                        "%Y%m%d", suffix[-12:-4]
                    ).date()
                    _extract_archive(config, archive, query, version)

        if not wait:
            break

    return response == remote_dirs, time.time() - download_start, to_date


def _extract_archive(
    config: custom_types.Config,
    archive: BinaryIO,
    query: custom_types.DownloadQuery,
    version: Literal["GGG2014", "GGG2020"],
) -> None:
    """Extracts, renames and stores archive members."""

    dst_path = f"{config.general.data_src_dirs.vertical_profiles}/{version}"
    with tarfile.open(fileobj=archive) as tar:
        for member in tar:
            name = member.name

            if not name.endswith((".map", ".mod", ".vmr")):
                # Skip (sub-)directories
                continue

            coordinates_slug = query.to_coordinates_slug()

            if version == "GGG2020":
                if name.endswith(".map"):
                    date, hour, type_ = name[47:55], name[55:57], "map"
                elif name.endswith(".mod"):
                    date, hour, type_ = name[35:43], name[43:45], "mod"
                elif name.endswith(".vmr"):
                    date, hour, type_ = name[39:47], name[47:49], "vmr"
                member.name = f"{date}{hour}_{coordinates_slug}.{type_}"
                # 2022010100_48N011E.map
                # 2022010103_48N011E.map
                # 20220101??_48N011E.map

            else:
                if name.endswith(".map"):
                    date, type_ = name[2:10], "map"
                elif name.endswith(".mod"):
                    date, type_ = name[5:13], "mod"
                member.name = f"{date}_{coordinates_slug}.{type_}"
                # 20220101_48N011E.map

            tar.extract(member, dst_path)
