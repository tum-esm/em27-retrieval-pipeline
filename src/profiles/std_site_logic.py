import datetime
import ftplib
import io
import os
import re
import rich.progress
from src import types, utils, profiles


def list_requested_data(
    config: types.Config,
    std_site_config: types.config.ProfilesGGG2020StandardSitesItemConfig,
) -> set[datetime.date]:
    assert config.profiles is not None
    from_date = std_site_config.from_date
    to_date = min(
        std_site_config.to_date,
        datetime.date.today() - datetime.timedelta(days=1),
    )
    if from_date > to_date:
        return set()
    else:
        return set(utils.functions.date_range(from_date, to_date))


def list_downloaded_data(
    config: types.Config,
    std_site_config: types.config.ProfilesGGG2020StandardSitesItemConfig,
) -> set[datetime.date]:
    downloaded_data: set[datetime.date] = set()

    cs = utils.text.get_coordinates_slug(
        lat=std_site_config.lat, lon=std_site_config.lon
    )
    r = re.compile(r"^\d{8,10}_" + cs + r"\.(map|mod|vmr)$")
    filenames: set[str] = set([
        f for f in os.listdir(
            os.path.
            join(config.general.data.atmospheric_profiles.root, "GGG2020")
        ) if r.match(f)
    ])
    dates: set[datetime.date] = set([
        d for d in [
            datetime.date(
                year=int(f[0 : 4]),
                month=int(f[4 : 6]),
                day=int(f[6 : 8]),
            ) for f in filenames
        ] if ((config.profiles.scope.from_date <= d) and
              (d <= config.profiles.scope.to_date))
    ])

    required_prefixes = [f"%Y%m%d{h:02d}" for h in range(0, 24, 3)]
    required_extensions = ["map", "mod", "vmr"]

    for d in dates:
        expected_filenames = set([
            f"{d.strftime(p)}_{cs}.{e}" for e in required_extensions
            for p in required_prefixes
        ])
        if expected_filenames.issubset(filenames):
            downloaded_data.add(d)

    return downloaded_data


def compute_missing_data(
    requested_data: set[datetime.date],
    downloaded_data: set[datetime.date],
) -> set[datetime.date]:
    return requested_data.difference(downloaded_data)
