from typing import BinaryIO, Callable
import time
import tarfile
import io
import ftplib
import datetime
from src import types, utils


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
            "tu",
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


def get_date_suffixes(
    config: types.Config,
    query: types.DownloadQuery,
    atmospheric_profile_model: types.AtmosphericProfileModel,
    get_current_datetime: Callable[
        [], datetime.datetime] = lambda: datetime.datetime.utcnow(),
) -> list[str]:
    """Generates date range suffixes up to config.max_day_delay
    days before utcnow()."""

    assert config.profiles is not None, "this is a bug in the code"

    sep = "_"
    worst_to_date = max(
        query.from_date,
        (get_current_datetime() - datetime.timedelta(days=10)).date(),
    )
    best_to_date = query.to_date

    if atmospheric_profile_model == "GGG2020":
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
    config: types.Config,
    query: types.DownloadQuery,
    ftp: ftplib.FTP,
    atmospheric_profile_model: types.AtmosphericProfileModel,
) -> bool:
    """Downloads .map, .mod and .vmr data.

    Searches exclusively for archive suffixes on the FTP server, given that
    job identifiers are unknown and sensor prefixes are irrelevant. Set 'wait'
    to True to attempt until the is found or config.download_timeout is
    exceeded. Sleeps config.download_sleep seconds in between each attempt.
    Returns whether successful, time.time() - upload_start and retrieved
    to date (as the server might truncate too recent requests).
    """

    assert config.profiles is not None, "this is a bug in the code"

    response: set[str] = set()
    date_suffixes = get_date_suffixes(config, query, atmospheric_profile_model)

    if atmospheric_profile_model == "GGG2020":
        remote_dirs = {"ginput-jobs"}
        cs = utils.text.get_coordinates_slug(query.lat, query.lon, verbose=True)
        suffixes = [f"{cs}_{d}.tgz" for d in date_suffixes]
    else:
        remote_dirs = {"upload/modfiles/tar/maps", "upload/modfiles/tar/mods"}
        cs = utils.text.get_coordinates_slug(query.lat, query.lon, verbose=True)
        suffixes = [f"{cs}_{d}.tar" for d in date_suffixes]

    download_start = time.time()
    while (response != remote_dirs and time.time() - download_start < 30):
        for remote_dir in remote_dirs - response:
            nlst = ftp.nlst(remote_dir)
            # Retrieve archive with largest date range
            suffix, archive_str = next(
                ((suffix, archive_str) for suffix in suffixes
                 for archive_str in nlst if archive_str.endswith(suffix)),
                (None, None),
            )

            if suffix is not None:
                # Retrieve data in-memory
                with io.BytesIO() as archive:
                    ftp.retrbinary(
                        f"RETR {archive_str}",
                        archive.write,
                    )
                    archive.seek(0)
                    response.add(remote_dir)
                    to_date = datetime.datetime.strptime(
                        suffix[-12 :-4],
                        "%Y%m%d",
                    ).date()
                    _extract_archive(
                        config, archive, query, atmospheric_profile_model
                    )

    return response == remote_dirs


def _extract_archive(
    config: types.Config,
    archive: BinaryIO,
    query: types.DownloadQuery,
    atmospheric_profile_model: types.AtmosphericProfileModel,
) -> None:
    """Extracts, renames and stores archive members."""

    dst_path = f"{config.general.data.atmospheric_profiles.root}/{atmospheric_profile_model}"
    with tarfile.open(fileobj=archive) as tar:
        for member in tar:
            name = member.name

            if not name.endswith((".map", ".mod", ".vmr")):
                # Skip (sub-)directories
                continue

            cs = utils.text.get_coordinates_slug(query.lat, query.lon)

            if atmospheric_profile_model == "GGG2020":
                if name.endswith(".map"):
                    date, hour, type_ = name[47 : 55], name[55 : 57], "map"
                elif name.endswith(".mod"):
                    date, hour, type_ = name[35 : 43], name[43 : 45], "mod"
                elif name.endswith(".vmr"):
                    date, hour, type_ = name[39 : 47], name[47 : 49], "vmr"
                member.name = f"{date}{hour}_{cs}.{type_}"
                # 2022010100_48N011E.map
                # 2022010103_48N011E.map
                # 20220101??_48N011E.map

            else:
                if name.endswith(".map"):
                    date, type_ = name[2 : 10], "map"
                elif name.endswith(".mod"):
                    date, type_ = name[5 : 13], "mod"
                member.name = f"{date}_{cs}.{type_}"
                # 20220101_48N011E.map

            tar.extract(member, dst_path)
