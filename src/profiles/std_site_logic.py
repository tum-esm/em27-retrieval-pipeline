import datetime
import ftplib
import io
import os
import re

import rich.progress
import tum_esm_utils

from src import profiles, types, utils


def list_requested_data(
    config: types.Config,
    std_site_config: types.config.ProfilesGGG2020StandardSitesItemConfig,
) -> set[datetime.date]:
    assert config.profiles is not None
    from_date = std_site_config.from_date
    to_date = min(
        std_site_config.to_date,
        (datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(hours=25)).date(),
    )
    if from_date > to_date:
        return set()
    else:
        return set(tum_esm_utils.timing.date_range(from_date, to_date))


def list_downloaded_data(
    config: types.Config,
    std_site_config: types.config.ProfilesGGG2020StandardSitesItemConfig,
) -> set[datetime.date]:
    assert config.profiles is not None
    downloaded_data: set[datetime.date] = set()

    cs = utils.text.get_coordinates_slug(lat=std_site_config.lat, lon=std_site_config.lon)
    r = re.compile(r"^\d{8,10}_" + cs + r"\.(map|mod|vmr)$")
    profile_root_dir = os.path.join(config.general.data.atmospheric_profiles.root, "GGG2020")
    filenames: set[str] = set(
        [
            f
            for f in os.listdir(
                profile_root_dir
            )
            if r.match(f)
        ]
    )
    years = set([f"{y:04d}" for y in range(1950, 2500)]).union(set(os.listdir(profile_root_dir)))
    for y in years:
        for m in range(1, 13):
            _d = os.path.join(profile_root_dir, y, f"{m:02d}")
            if os.path.isdir(_d):
                filenames.update([f for f in os.listdir(_d) if r.match(f)])
    
    dates: set[datetime.date] = set(
        [
            d
            for d in [
                datetime.date(
                    year=int(f[0:4]),
                    month=int(f[4:6]),
                    day=int(f[6:8]),
                )
                for f in filenames
            ]
            if ((std_site_config.from_date <= d) and (d <= std_site_config.to_date))
        ]
    )

    required_prefixes = [f"%Y%m%d{h:02d}" for h in range(0, 24, 3)]
    required_extensions = ["map", "mod", "vmr"]

    for d in dates:
        expected_filenames = set(
            [f"{d.strftime(p)}_{cs}.{e}" for e in required_extensions for p in required_prefixes]
        )
        if expected_filenames.issubset(filenames):
            downloaded_data.add(d)

    return downloaded_data


def compute_missing_data(
    requested_data: set[datetime.date],
    downloaded_data: set[datetime.date],
) -> set[datetime.date]:
    return requested_data.difference(downloaded_data)


def download_data(
    config: types.Config,
    ftp: ftplib.FTP,
) -> None:
    assert config.profiles is not None
    with rich.progress.Progress() as progress:
        task = progress.add_task(
            description="Processing standard sites",
            total=len(config.profiles.GGG2020_standard_sites),
        )
        for std_site_config in config.profiles.GGG2020_standard_sites:
            progress.print(f"Processing {std_site_config.model_dump_json(indent=4)}")
            requested_data = list_requested_data(config, std_site_config)
            downloaded_data = list_downloaded_data(config, std_site_config)
            missing_data = compute_missing_data(
                requested_data=requested_data,
                downloaded_data=downloaded_data,
            )
            progress.print(
                f"Requested days: {len(requested_data)}\n"
                f"Downloaded days: {len(downloaded_data)}\n"
                f"Missing days (req - dow): {len(missing_data)}"
            )
            if len(missing_data) > 0:
                subtask = progress.add_task(
                    description=f"Downloading {std_site_config.identifier}",
                    total=len(missing_data),
                )
                tarballs_on_server = ftp.nlst(
                    f"ginput-std-sites/tarballs/{std_site_config.identifier}/"
                )
                for date in sorted(missing_data):
                    progress.print(date.strftime("%Y-%m-%d"))
                    try:
                        filename = next(
                            filter(
                                lambda f: f.endswith(date.strftime("%Y%m%d.tgz")),
                                tarballs_on_server,
                            )
                        )
                        print("Found!")
                        with io.BytesIO() as archive:
                            ftp.retrbinary(
                                f"RETR {filename}",
                                archive.write,
                            )
                            archive.seek(0)
                            profiles.download_logic.extract_archive(
                                config=config,
                                archive=archive,
                                lat=std_site_config.lat,
                                lon=std_site_config.lon,
                                atmospheric_profile_model="GGG2020",
                            )
                    except StopIteration:
                        progress.print("No tarball")
                    progress.advance(subtask)
            else:
                progress.print("No data to download")
            progress.advance(task)
