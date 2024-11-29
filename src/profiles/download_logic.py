import ftplib
import io
import tarfile
from typing import BinaryIO

import rich.progress

from src import types, utils


def download_data(
    config: types.Config,
    queries: list[types.DownloadQuery],
    ftp: ftplib.FTP,
    atmospheric_profile_model: types.AtmosphericProfileModel,
) -> list[types.DownloadQuery]:
    """Downloads data from 'ccycle.gps.caltech.edu' and returns a list of
    queries that were fulfilled."""

    tarballs_on_server: list[str]
    if atmospheric_profile_model == "GGG2020":
        tarballs_on_server = ftp.nlst("ginput-jobs")
    else:
        tarballs_on_server = ftp.nlst("upload/modfiles/tar/maps") + ftp.nlst(
            "upload/modfiles/tar/mods"
        )

    # GGG2014: /upload/modfiles/tar/mods/mods_48N011E_20231211_20231217.tar
    # GGG2020: /ginput-jobs/job_000034641_tu_48.00N_12.00E_20221001-20221008.tgz

    fulfilled_queries: list[types.DownloadQuery] = []

    with rich.progress.Progress() as progress:
        for query in progress.track(queries, description="Downloading ..."):
            progress.print(f"Downloading {query}")

            cs_verbose = utils.text.get_coordinates_slug(query.lat, query.lon, verbose=True)
            cs_nonverbose = utils.text.get_coordinates_slug(query.lat, query.lon, verbose=False)
            ds = query.from_date.strftime("%Y%m%d")
            tarballs_to_download = [
                t
                for t in tarballs_on_server
                if ((f"{cs_verbose}_{ds}" in t) or (f"{cs_nonverbose}_{ds}" in t))
            ]
            if atmospheric_profile_model == "GGG2020":
                if len(tarballs_to_download) >= 1:
                    fulfilled_queries.append(query)
                    progress.print("Found!")
                else:
                    progress.print("Not found!")
            else:
                if len(tarballs_to_download) >= 2:
                    fulfilled_queries.append(query)
                    progress.print("Found!")
                else:
                    progress.print("Not found!")
            for t in tarballs_to_download:
                with io.BytesIO() as archive:
                    ftp.retrbinary(
                        f"RETR {t}",
                        archive.write,
                    )
                    archive.seek(0)
                    extract_archive(
                        config=config,
                        archive=archive,
                        lat=query.lat,
                        lon=query.lon,
                        atmospheric_profile_model=atmospheric_profile_model,
                    )

    return fulfilled_queries


def extract_archive(
    config: types.Config,
    archive: BinaryIO,
    lat: float,
    lon: float,
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

            cs = utils.text.get_coordinates_slug(lat, lon)

            if atmospheric_profile_model == "GGG2020":
                basename = name.split("/")[-1]
                extension = basename.split(".")[-1]
                assert extension in ["map", "mod", "vmr"], f"Unexpected extension: {extension}"
                if extension == "map":
                    date = basename.split("_")[-1][:8]
                    hour = basename.split("_")[-1][8:10]
                elif extension == "mod":
                    date = basename.split("_")[1][:8]
                    hour = basename.split("_")[1][8:10]
                elif extension == "vmr":
                    date = basename.split("_")[1][:8]
                    hour = basename.split("_")[1][8:10]
                member.name = f"{date}{hour}_{cs}.{extension}"
                # 2022010100_48N011E.map
                # 2022010103_48N011E.map
                # 20220101??_48N011E.map

            else:
                if name.endswith(".map"):
                    date, type_ = name[2:10], "map"
                elif name.endswith(".mod"):
                    date, type_ = name[5:13], "mod"
                member.name = f"{date}_{cs}.{type_}"
                # 20220101_48N011E.map

            tar.extract(member, dst_path)
