from typing import BinaryIO
import tarfile
import io
import ftplib
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
        tarballs_on_server = ftp.nlst("upload/modfiles/tar/maps"
                                     ) + ftp.nlst("upload/modfiles/tar/mods")

    # GGG2020: /ginput-jobs/job_000034641_tu_48.00N_12.00E_20221001-20221008.tgz

    fulfilled_queries: list[types.DownloadQuery] = []

    with rich.progress.Progress() as progress:
        for query in progress.track(queries, description=f"Downloading ..."):
            progress.print(f"Downloading {query}")

            cs = utils.text.get_coordinates_slug(
                query.lat, query.lon, verbose=True
            )
            ds = query.from_date.strftime("%Y%m%d")
            tarballs_to_download = [
                t for t in tarballs_on_server if f"{cs}_{ds}" in t
            ]
            if atmospheric_profile_model == "GGG2020":
                if len(tarballs_to_download) >= 1:
                    fulfilled_queries.append(query)
            else:
                if len(tarballs_to_download) >= 2:
                    fulfilled_queries.append(query)
            for t in tarballs_to_download:
                with io.BytesIO() as archive:
                    ftp.retrbinary(
                        f"RETR {t}",
                        archive.write,
                    )
                    archive.seek(0)
                    _extract_archive(
                        config=config,
                        archive=archive,
                        lat=query.lat,
                        lon=query.lon,
                        atmospheric_profile_model=atmospheric_profile_model,
                    )

    return fulfilled_queries


def _extract_archive(
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
