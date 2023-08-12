import datetime
import os
from typing import Literal, Optional
import tum_esm_em27_metadata
from src import custom_types


def generate_download_queries(
    config: custom_types.Config,
    version: Literal["GGG2014", "GGG2020"],
    em27_metadata: Optional[
        tum_esm_em27_metadata.interfaces.EM27MetadataInterface
    ] = None,
) -> list[custom_types.DownloadQuery]:
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

    if config.vertical_profiles is None:
        return []

    # Request sensor and location data
    if em27_metadata is None:
        em27_metadata = tum_esm_em27_metadata.load_from_github(
            github_repository=config.general.location_data.github_repository,
            access_token=config.general.location_data.access_token,
        )

    # dict[lat][lon] = [DownloadQuery(...), ...]
    requested_dates: dict[float, dict[float, list[custom_types.DownloadQuery]]] = {}

    for sensor in em27_metadata.sensors:
        for sensor_location in sensor.locations:
            # do not consider sensor locations that are outside of the request scope
            if (
                sensor_location.to_datetime.date()
                < config.vertical_profiles.request_scope.from_date
            ) or (
                sensor_location.from_datetime.date()
                > config.vertical_profiles.request_scope.to_date
            ):
                continue

            # trim reqested dates to request scope
            from_date = config.vertical_profiles.request_scope.from_date
            to_date = config.vertical_profiles.request_scope.to_date
            if sensor_location.from_datetime.date() > from_date:
                from_date = sensor_location.from_datetime.date()
            if sensor_location.to_datetime.date() < to_date:
                to_date = sensor_location.to_datetime.date()

            # get location data
            location = next(
                l
                for l in em27_metadata.locations
                if l.location_id == sensor_location.location_id
            )

            # Iterate over individual days and add sensor
            current_date = from_date
            while current_date <= to_date:
                if len(requested_dates[location.lat][location.lon]) == 0:
                    requested_dates[location.lat][location.lon] = [
                        custom_types.DownloadQuery(
                            lat=location.lat,
                            lon=location.lon,
                            from_date=current_date,
                            to_date=current_date,
                        )
                    ]
                elif (
                    requested_dates[location.lat][location.lon][-1].to_date
                    - datetime.timedelta(days=1)
                    == current_date
                ):
                    requested_dates[location.lat][location.lon][
                        -1
                    ].to_date = current_date
                else:
                    requested_dates[location.lat][location.lon].append(
                        custom_types.DownloadQuery(
                            lat=location.lat,
                            lon=location.lon,
                            from_date=current_date,
                            to_date=current_date,
                        )
                    )
                current_date = current_date + datetime.timedelta(days=1)

    # merges overlapping queries into single queries
    download_queries: list[custom_types.DownloadQuery] = []
    for lat in requested_dates.keys():
        for lon in requested_dates[lat].keys():
            download_queries += _compress_query_list(requested_dates[lat][lon])

    # removes the days from queries where the data is already present locally
    fresh_download_queries: list[custom_types.DownloadQuery] = []
    dst_path = os.path.join(config.general.data_src_dirs.vertical_profiles, version)
    present_files = os.listdir(dst_path)
    for dq in download_queries:
        present_dates: list[datetime.date] = []
        for f in present_files:
            try:
                assert f.endswith(dq.to_coordinates_slug())
                assert os.path.isdir(os.path.join(dst_path, f))
                date = datetime.datetime.strptime(f, "%Y-%m-%d").date()
                present_dates.append(date)
            except (AssertionError, ValueError):
                pass
        fresh_download_queries += _remove_present_dates(dq, present_dates)

    # make queries not be longer than 28 days
    chunked_download_queries: list[custom_types.DownloadQuery] = []
    for dq in fresh_download_queries:
        chunked_download_queries += _split_large_queries(dq, max_days_per_query=28)

    return chunked_download_queries


def _remove_present_dates(
    dq: custom_types.DownloadQuery, present_dates: list[datetime.date]
) -> list[custom_types.DownloadQuery]:
    """Remove dates from the query that are already present locally"""

    present_dates = list(
        sorted(filter(lambda d: dq.from_date <= d <= dq.to_date, present_dates))
    )
    while True:
        if len(present_dates) == 0:
            return [dq]

        if present_dates[0] == dq.from_date:
            dq.from_date = dq.from_date + datetime.timedelta(days=1)
            present_dates.pop(0)
            continue
        if present_dates[-1] == dq.to_date:
            dq.to_date = dq.to_date - datetime.timedelta(days=1)
            present_dates.pop(-1)
            continue

        first_date = present_dates.pop(0)

        return [
            custom_types.DownloadQuery(
                lat=dq.lat,
                lon=dq.lon,
                from_date=dq.from_date,
                to_date=first_date - datetime.timedelta(days=1),
            ),
            *_remove_present_dates(
                custom_types.DownloadQuery(
                    lat=dq.lat,
                    lon=dq.lon,
                    from_date=first_date + datetime.timedelta(days=1),
                    to_date=dq.to_date,
                ),
                present_dates=present_dates,
            ),
        ]


def _split_large_queries(
    dq: custom_types.DownloadQuery, max_days_per_query: int = 28
) -> list[custom_types.DownloadQuery]:
    """If the queries are longer than the specified number of days,
    split them into multiple queries."""

    dt = dq.to_date - dq.from_date

    if dt.days <= max_days_per_query:
        return [dq]

    return [
        custom_types.DownloadQuery(
            lat=dq.lat,
            lon=dq.lon,
            from_date=dq.from_date,
            to_date=dq.from_date + datetime.timedelta(days=max_days_per_query - 1),
        ),
        *_split_large_queries(
            custom_types.DownloadQuery(
                lat=dq.lat,
                lon=dq.lon,
                from_date=dq.from_date + datetime.timedelta(days=max_days_per_query),
                to_date=dq.to_date,
            ),
            max_days_per_query=max_days_per_query,
        ),
    ]


def _compress_query_list(
    queries: list[custom_types.DownloadQuery],
) -> list[custom_types.DownloadQuery]:
    """Compress a list of queries by merging queries that are
    asjacent or overlapping into long queries."""

    if len(queries) < 2:
        return queries

    queries = list(sorted(queries, key=lambda d: d.from_date))

    while True:
        overlapping_queries = list(
            filter(
                lambda d: d.from_date
                <= (queries[0].to_date + datetime.timedelta(days=1)),
                queries[1:],
            )
        )
        if len(overlapping_queries) > 0:
            queries[0].end_date = max([q.to_date for q in overlapping_queries])
            queries = [queries[0], *queries[len(overlapping_queries) + 1 :]]
            continue

        return [
            queries[0],
            *_compress_query_list(queries[1:]),
        ]
