from __future__ import annotations

import copy
import datetime
import os
import re
from typing import Optional

import em27_metadata
import pydantic
import tum_esm_utils

from src import types, utils

from .cache import DownloadQueryCache


class ProfilesQueryTimePeriod(pydantic.BaseModel):
    from_date: datetime.date
    to_date: datetime.date


class ProfilesQueryLocation(pydantic.BaseModel):
    lat: int
    lon: int

    def __hash__(self) -> int:
        return hash((self.lat, self.lon))


def list_downloaded_data(
    config: types.Config,
    atmospheric_profile_model: types.AtmosphericProfileModel,
) -> dict[ProfilesQueryLocation, set[datetime.date]]:
    assert config.profiles is not None
    assert config.profiles.scope is not None
    downloaded_data: dict[ProfilesQueryLocation, set[datetime.date]] = {}

    profile_root_dir = os.path.join(
        config.general.data.atmospheric_profiles.root, atmospheric_profile_model
    )

    r = re.compile(r"^\d{8,10}_\d{2}(N|S)\d{3}(E|W)\.(map|mod|vmr)$")
    filenames: set[str] = set([f for f in os.listdir(profile_root_dir) if r.match(f)])

    # starting with 1.7.0, the default way of storing atmospheric profiles
    # is to store them in subdirectories by year and month. However, only newly
    # downloaded data will be stored in this way. Data in the old format can still
    # be used. There is a script to move all data from the previous paths to
    # the new paths, but this should not be done automatically.
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
            if ((config.profiles.scope.from_date <= d) and (d <= config.profiles.scope.to_date))
        ]
    )
    locations: set[ProfilesQueryLocation] = set(
        [
            ProfilesQueryLocation(
                lat=int(f.split("_")[1][0:2]) * (-1 if f.split("_")[1][2] == "S" else 1),
                lon=int(f.split("_")[1][3:6]) * (-1 if f.split("_")[1][6] == "W" else 1),
            )
            for f in filenames
        ]
    )

    required_prefixes: list[str]
    required_extensions: list[str]
    if atmospheric_profile_model == "GGG2014":
        required_prefixes = ["%Y%m%d"]
        required_extensions = ["map", "mod"]
    else:
        required_prefixes = [f"%Y%m%d{h:02d}" for h in range(0, 24, 3)]
        required_extensions = ["map", "mod", "vmr"]

    for location in locations:
        cs = utils.text.get_coordinates_slug(lat=location.lat, lon=location.lon)
        for d in dates:
            expected_filenames = set(
                [
                    f"{d.strftime(p)}_{cs}.{e}"
                    for e in required_extensions
                    for p in required_prefixes
                ]
            )
            if expected_filenames.issubset(filenames):
                if location not in downloaded_data.keys():
                    downloaded_data[location] = set()
                downloaded_data[location].add(d)

    return downloaded_data


def list_desired_data(
    config: types.Config,
    em27_metadata_interface: em27_metadata.interfaces.EM27MetadataInterface,
) -> dict[ProfilesQueryLocation, set[datetime.date]]:
    assert config.profiles is not None
    assert config.profiles.scope is not None
    requested_data: dict[ProfilesQueryLocation, set[datetime.date]] = {}

    for location_id in config.profiles.scope.force_download_locations:
        try:
            location = next(
                filter(
                    lambda _l: _l.location_id == location_id,
                    em27_metadata_interface.locations.root,
                )
            )
        except StopIteration:
            raise ValueError(
                f"Location with ID {location_id} not found in metadata. Please check your configuration."
            )

        query_location = ProfilesQueryLocation(lat=round(location.lat), lon=round(location.lon))
        if query_location not in requested_data.keys():
            requested_data[query_location] = set()
        
        cropped_to_date = min(
            config.profiles.scope.to_date,
            (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=36)).date(),
        )
        if config.profiles.scope.from_date <= cropped_to_date:
            requested_data[query_location].update(
                tum_esm_utils.timing.date_range(
                    from_date=config.profiles.scope.from_date,
                    to_date=cropped_to_date,
                )
            )

    for sensor in em27_metadata_interface.sensors.root:
        for sensor_setup in sensor.setups:
            atmospheric_profile_location_id = sensor_setup.value.location_id
            if sensor_setup.value.atmospheric_profile_location_id is not None:
                atmospheric_profile_location_id = sensor_setup.value.atmospheric_profile_location_id
            location = next(
                filter(
                    lambda _l: _l.location_id == atmospheric_profile_location_id,
                    em27_metadata_interface.locations.root,
                )
            )

            query_location = ProfilesQueryLocation(lat=round(location.lat), lon=round(location.lon))
            if query_location not in requested_data.keys():
                requested_data[query_location] = set()

            from_date = max(
                config.profiles.scope.from_date,
                sensor_setup.from_datetime.date(),
            )
            to_date = min(
                config.profiles.scope.to_date,
                sensor_setup.to_datetime.date(),
                (
                    datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=36)
                ).date(),
            )
            if from_date <= to_date:
                requested_data[query_location].update(
                    tum_esm_utils.timing.date_range(from_date=from_date, to_date=to_date)
                )

    return requested_data


def compute_missing_data(
    desired_data: dict[ProfilesQueryLocation, set[datetime.date]],
    downloaded_data: dict[ProfilesQueryLocation, set[datetime.date]],
) -> dict[ProfilesQueryLocation, set[datetime.date]]:
    missing_data: dict[ProfilesQueryLocation, set[datetime.date]] = {}

    for location in desired_data.keys():
        if location not in downloaded_data.keys():
            missing_data[location] = desired_data[location]
        else:
            missing_data[location] = set(desired_data[location]).difference(
                downloaded_data[location]
            )

    return missing_data


def remove_already_requested_data(
    missing_data: dict[ProfilesQueryLocation, set[datetime.date]],
    atmospheric_profile_model: types.AtmosphericProfileModel,
) -> dict[ProfilesQueryLocation, set[datetime.date]]:
    cache = DownloadQueryCache.load()
    active_queries = cache.get_active_queries(atmospheric_profile_model)
    for location in list(missing_data.keys()):
        already_requested_dates: set[datetime.date] = set()
        for q in active_queries:
            if q.lat == location.lat and q.lon == location.lon:
                already_requested_dates.update(
                    tum_esm_utils.timing.date_range(from_date=q.from_date, to_date=q.to_date)
                )
        missing_data[location].difference_update(already_requested_dates)
        if len(missing_data[location]) == 0:
            missing_data.pop(location)
    return missing_data


def remove_std_site_data(
    config: types.Config,
    missing_data: dict[ProfilesQueryLocation, set[datetime.date]],
) -> dict[ProfilesQueryLocation, set[datetime.date]]:
    assert config.profiles is not None
    filtered_data: dict[ProfilesQueryLocation, set[datetime.date]] = copy.deepcopy(missing_data)
    for std_site_config in config.profiles.GGG2020_standard_sites:
        location = ProfilesQueryLocation(
            lat=round(std_site_config.lat),
            lon=round(std_site_config.lon),
        )
        if location in filtered_data.keys():
            filtered_data[location].difference_update(
                tum_esm_utils.timing.date_range(
                    from_date=std_site_config.from_date,
                    to_date=std_site_config.to_date,
                )
            )
            if len(filtered_data[location]) == 0:
                filtered_data.pop(location)
    return filtered_data


def compute_time_periods(missing_data: set[datetime.date]) -> list[ProfilesQueryTimePeriod]:
    mondays = set([d - datetime.timedelta(days=d.weekday()) for d in missing_data])
    time_periods: list[ProfilesQueryTimePeriod] = []
    for d in mondays:
        dates = set([d + datetime.timedelta(days=i) for i in range(0, 7)]).intersection(
            missing_data
        )
        time_periods.append(ProfilesQueryTimePeriod(from_date=min(dates), to_date=max(dates)))
    return time_periods


def generate_download_queries(
    config: types.Config,
    atmospheric_profile_model: types.AtmosphericProfileModel,
    em27_metadata_interface: Optional[em27_metadata.interfaces.EM27MetadataInterface] = None,
) -> list[types.DownloadQuery]:
    """Returns a list of `DownloadQuery` objects for which the
    data has not been downloaded yet. Example:

    ```python
    [
        DownloadQuery(lat=48, lon=11, from_date=2020-01-01, to_date=2020-01-03),
        DownloadQuery(lat=48, lon=12, from_date=2020-01-01, to_date=2020-01-08),
    ]
    ```"""

    assert config.profiles is not None

    if em27_metadata_interface is None:
        em27_metadata_interface = utils.metadata.load_local_em27_metadata_interface()
        if em27_metadata_interface is not None:
            print("Found local metadata")
        else:
            print("Did not find local metadata -> fetching metadata from GitHub")
            assert config.general.metadata is not None, "Remote metadata not configured"
            em27_metadata_interface = em27_metadata.load_from_github(
                github_repository=config.general.metadata.github_repository,
                access_token=config.general.metadata.access_token,
            )
            print("Successfully fetched metadata from GitHub")

    missing_data = compute_missing_data(
        desired_data=list_desired_data(
            config=config,
            em27_metadata_interface=em27_metadata_interface,
        ),
        downloaded_data=list_downloaded_data(
            config=config,
            atmospheric_profile_model=atmospheric_profile_model,
        ),
    )
    data_to_request = missing_data
    if atmospheric_profile_model == "GGG2020":
        data_to_request = remove_std_site_data(
            config=config,
            missing_data=remove_already_requested_data(
                missing_data=missing_data,
                atmospheric_profile_model=atmospheric_profile_model,
            ),
        )
    download_queries: list[types.DownloadQuery] = []
    for location, dates in data_to_request.items():
        download_queries.extend(
            [
                types.DownloadQuery(
                    lat=location.lat,
                    lon=location.lon,
                    from_date=tp.from_date,
                    to_date=tp.to_date,
                )
                for tp in compute_time_periods(dates)
            ]
        )

    return sorted(download_queries, key=lambda q: q.from_date, reverse=True)
