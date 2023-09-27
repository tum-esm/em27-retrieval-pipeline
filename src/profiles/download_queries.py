import datetime
import os
from typing import Literal, Optional
import tum_esm_em27_metadata
import src


def generate_download_queries(
    config: src.utils.config.Config,
    version: Literal["GGG2014", "GGG2020"],
    em27_metadata: Optional[
        tum_esm_em27_metadata.interfaces.EM27MetadataInterface] = None,
) -> list[src.utils.types.DownloadQuery]:
    """Returns a dictionary that maps query locations to sensor sets.
    Sensor sets map days to a all sensors ids that were located at
    the query location on that day. Note that query locations store
    rounded coordinates and thus might bundle multiple locations.

    Example:

    ```python
    [
        DownloadQuery(lat=48, lon=11, start_date=2020-01-01, end_date=2020-01-03),
        DownloadQuery(lat=48, lon=12, start_date=2020-01-01, end_date=2020-01-08),
    ]
    ```"""

    if config.profiles is None:
        return []

    # Request sensor and location data
    if em27_metadata is None:
        em27_metadata = tum_esm_em27_metadata.load_from_github(
            github_repository=config.general.location_data.github_repository,
            access_token=config.general.location_data.access_token,
        )

    # dict[lat][lon] = {datetime.date, ...}
    query_dates: dict[int, dict[int, set[datetime.date]]] = {}

    for sensor in em27_metadata.sensors:
        for sensor_location in sensor.locations:
            # do not consider sensor locations that are outside of the request scope
            if (
                sensor_location.to_datetime.date()
                < config.profiles.request_scope.from_date
            ) or (
                sensor_location.from_datetime.date()
                > config.profiles.request_scope.to_date
            ):
                continue

            # trim reqested dates to request scope
            from_date = config.profiles.request_scope.from_date
            to_date = min(
                config.profiles.request_scope.to_date,
                datetime.date.today() - datetime.timedelta(days=4)
            )
            if sensor_location.from_datetime.date() > from_date:
                from_date = sensor_location.from_datetime.date()
            if sensor_location.to_datetime.date() < to_date:
                to_date = sensor_location.to_datetime.date()

            # get location data
            location = next(
                l for l in em27_metadata.locations
                if l.location_id == sensor_location.location_id
            )
            lat = round(location.lat)
            lon = round(location.lon)
            if lat not in query_dates.keys():
                query_dates[lat] = {}
            if lon not in query_dates[lat].keys():
                query_dates[lat][lon] = set()

            # Iterate over individual days and add sensor
            for date in [
                from_date + datetime.timedelta(days=i)
                for i in range((to_date - from_date).days + 1)
            ]:
                query_dates[lat][lon].add(date)

    print(
        "Total queried days:",
        sum([
            len(query_dates[lat][lon]) for lat in query_dates.keys()
            for lon in query_dates[lat].keys()
        ])
    )

    # remove queries where data is already present locally
    for lat in query_dates.keys():
        for lon in query_dates[lat].keys():
            filtered_queries: set[datetime.date] = set()
            for date in query_dates[lat][lon]:
                date_slug = date.strftime("%Y%m%d")
                coordinate_slug = src.utils.functions.get_coordinates_slug(
                    lat, lon
                )
                if version == "GGG2014":
                    output_files = [
                        os.path.join(
                            config.general.data_src_dirs.profiles,
                            version,
                            f"{date_slug}_{coordinate_slug}.{ending}",
                        ) for ending in ["map", "mod"]
                    ]
                else:
                    output_files = [
                        os.path.join(
                            config.general.data_src_dirs.profiles,
                            version,
                            f"{date_slug}{time:02d}_{coordinate_slug}.{ending}",
                        ) for ending in ["map", "mod", "vmr"]
                        for time in [0, 3, 6, 9, 12, 15, 18, 21]
                    ]
                if not all([os.path.isfile(f) for f in output_files]):
                    filtered_queries.add(date)
            query_dates[lat][lon] = filtered_queries

    print(
        "Newly queried days:",
        sum([
            len(query_dates[lat][lon]) for lat in query_dates.keys()
            for lon in query_dates[lat].keys()
        ])
    )

    total_download_queries: list[src.utils.types.DownloadQuery] = []

    for lat in query_dates.keys():
        for lon in query_dates[lat].keys():
            download_queries: list[src.utils.types.DownloadQuery] = []
            for date in sorted(query_dates[lat][lon]):
                if len(download_queries) == 0:
                    download_queries.append(
                        src.utils.types.DownloadQuery(
                            lat=lat, lon=lon, from_date=date, to_date=date
                        )
                    )
                else:
                    current_query = download_queries[-1]
                    start_new_query_block = ((
                        date
                        > (current_query.to_date + datetime.timedelta(days=1))
                    ) or (current_query.to_date - current_query.from_date).days
                                             >= 27)
                    if start_new_query_block:
                        download_queries.append(
                            src.utils.types.DownloadQuery(
                                lat=lat, lon=lon, from_date=date, to_date=date
                            )
                        )
                    else:
                        download_queries[-1].to_date = date

            total_download_queries.extend(download_queries)

    return total_download_queries
