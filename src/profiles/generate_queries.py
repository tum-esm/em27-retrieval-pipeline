from __future__ import annotations
from typing import Optional
import os
import re
import em27_metadata
import pydantic
import datetime
from src import types, utils


class _TimePeriod(pydantic.BaseModel):
    from_date: datetime.date
    to_date: datetime.date
    requested_dates: list[datetime.date]

    @staticmethod
    def generate_periods(
        requested_dates: set[datetime.date]
    ) -> list[_TimePeriod]:
        """Given a start and end date, construct a list of time periods
        that cover the whole range. The time periods will be weeks, starting
        on Monday and ending on Sunday."""
        time_periods: list[_TimePeriod] = []
        for d in sorted(requested_dates):
            if (len(time_periods) == 0) or (d > time_periods[-1].to_date):
                time_periods.append(
                    _TimePeriod(
                        from_date=d - datetime.timedelta(days=d.weekday()),
                        to_date=d + datetime.timedelta(days=6 - d.weekday()),
                        requested_dates=[d]
                    )
                )
            else:
                time_periods[-1].requested_dates.append(d)

        for tp in time_periods:
            tp.from_date = min(tp.requested_dates)
            tp.to_date = max(tp.requested_dates)
        return time_periods


class _Location(pydantic.BaseModel):
    lat: float
    lon: float

    def __hash__(self) -> int:
        return hash((int(self.lat), int(self.lon)))


def generate_download_queries(
    config: types.Config,
    atmospheric_profile_model: types.AtmosphericProfileModel,
    em27_metadata_storage: Optional[
        em27_metadata.interfaces.EM27MetadataInterface] = None,
) -> list[types.DownloadQuery]:
    """Returns a list of `DownloadQuery` objects for which the
    data has not been downloaded yet. Example:

    ```python
    [
        DownloadQuery(lat=48, lon=11, from_date=2020-01-01, to_date=2020-01-03),
        DownloadQuery(lat=48, lon=12, from_date=2020-01-01, to_date=2020-01-08),
    ]
    ```"""

    # if profiles download is not configured
    if config.profiles is None:
        return []

    # request sensor and location data
    if em27_metadata_storage is None:
        em27_metadata_storage = em27_metadata.load_from_github(
            github_repository=config.general.metadata.github_repository,
            access_token=config.general.metadata.access_token,
        )

    # dates_by_location[lat][lon] = [...]
    dates_by_location: dict[
        _Location,
        list[em27_metadata.types.SensorTypes.Location],
    ] = {}

    for sensor in em27_metadata_storage.sensors:
        for sensor_location in sensor.locations:
            location = next(
                filter(
                    lambda l: l.location_id == sensor_location.location_id,
                    em27_metadata_storage.locations
                )
            )

            l = _Location(lat=location.lat, lon=location.lon)
            if l not in dates_by_location.keys():
                dates_by_location[l] = []
            dates_by_location[l].append(sensor_location)

    print(
        f"Bundeled location data into {len(dates_by_location)} " +
        f"query locations (rounded lat/lon): {dates_by_location}"
    )

    downloaded_dates_by_location: dict[_Location, set[datetime.date]] = {}

    # GGG2014: /mnt/dss-0002/atmospheric-profiles/GGG2014/20150826_48N012E.map
    # GGG2020: /mnt/dss-0002/atmospheric-profiles/GGG2020/2022100100_48N011E.map
    filenames = set(
        os.listdir(
            os.path.join(
                config.general.data.atmospheric_profiles.root,
                atmospheric_profile_model,
            )
        )
    )
    locations: list[_Location] = [
        _Location(
            lat=int(f.split("_")[1][0 : 2]) *
            (-1 if f.split("_")[1][2] == "S" else 1),
            lon=int(f.split("_")[1][3 : 6]) *
            (-1 if f.split("_")[1][6] == "W" else 1),
        ) for f in filenames
        if re.match(r"\d{8,10}_\d{2}(N|S)\d{3}(E|W)\.map", f)
    ]
    for l in locations:
        cs = utils.text.get_coordinates_slug(lat=l.lat, lon=l.lon)
        dates: list[datetime.date] = [
            datetime.date(
                year=int(f[0 : 4]),
                month=int(f[4 : 6]),
                day=int(f[6 : 8]),
            ) for f in filenames if re.match(r"\d{8,10}_" + cs + r"\.map", f)
        ]
        downloaded_dates: set[datetime.date] = set()
        for date in dates:
            expected_filenames: set[str]
            if atmospheric_profile_model == "GGG2014":
                expected_filenames = set([
                    f"{date.strftime('%Y%m%d')}_{cs}.{p}"
                    for p in ["map", "mod"]
                ])
            if atmospheric_profile_model == "GGG2020":
                expected_filenames = set([
                    f"{date.strftime('%Y%m%d')}{t:02d}_{cs}.{p}"
                    for t in range(0, 24, 3) for p in ["map", "mod", "vmr"]
                ])
            if expected_filenames.issubset(filenames):
                downloaded_dates.add(date)
        downloaded_dates_by_location[l] = downloaded_dates

    download_queries: list[types.DownloadQuery] = []

    # construct time periods
    for l, sensor_locations in dates_by_location.items():
        requested_dates: set[datetime.date] = set()
        for sensor_location in sensor_locations:
            requested_dates.update(
                utils.functions.date_range(
                    from_date=sensor_location.from_datetime.date(),
                    to_date=sensor_location.to_datetime.date(),
                )
            )
        requested_dates = set([
            d for d in requested_dates if (
                d >= config.profiles.scope.from_date and
                d <= config.profiles.scope.to_date and d < datetime.date.today()
            )
        ])
        missing_dates = requested_dates.difference(
            downloaded_dates_by_location.get(l, set())
        )
        print(f"Location {l} has {len(missing_dates)} missing dates")

        new_download_queries = [
            types.DownloadQuery(
                lat=int(l.lat),
                lon=int(l.lon),
                from_date=tp.from_date,
                to_date=tp.to_date,
            ) for tp in
            _TimePeriod.generate_periods(requested_dates=missing_dates)
        ]
        print(f"Location {l} has {len(new_download_queries)} new queries")

        download_queries.extend(new_download_queries)

    return download_queries
