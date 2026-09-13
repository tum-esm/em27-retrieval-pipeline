import datetime
from typing import Optional

import tum_esm_utils

from . import types as em27_metadata_types


class EM27MetadataInterface:
    def __init__(
        self,
        locations: em27_metadata_types.LocationMetadataList,
        sensors: em27_metadata_types.SensorMetadataList,
        campaigns: em27_metadata_types.CampaignMetadataList = em27_metadata_types.CampaignMetadataList(
            root=[]
        ),
        events: em27_metadata_types.EventMetadataList = em27_metadata_types.EventMetadataList(
            root=[]
        ),
    ) -> None:
        """Create a new EM27MetadataInterface object.

        During the instantiation, the integrity of the metadata is checked by
        running the following tests:

            * Location IDs are unique
            * Sensor IDs are unique
            * Campaign IDs are unique
            * All location IDs referenced in sensors.json exist
            * All sensor IDs referenced in campaigns.json exist
            * All location IDs referenced in campaigns.json exist
            * All time series elements in sensors.json have from_datetime < to_datetime
            * The time series in sensors.json are sorted
            * The time series in sensors.json have no overlaps

        Args:
            locations:  A list of `LocationMetadata` objects.
            sensors:    A list of `SensorMetadata` objects.
            campaigns:  A list of `CampaignMetadata` objects.

        Returns:  An metadata object containing all the metadata that can now be queried
                  locally using `metadata.get`.

        Raises:
            pydantic.ValidationError:  If the metadata integrity checks fail.
        """

        self.locations = locations
        self.sensors = sensors
        self.campaigns = campaigns
        self.events = events

        # reference existence in sensors.json
        for s1 in sensors.root:
            for l1 in s1.deployments:
                assert l1.location_id in locations.location_ids, (
                    f"unknown location id {l1.location_id}"
                )

        # reference existence in campaigns.json
        for c1 in campaigns.root:
            for _sid in c1.sensor_ids:
                assert _sid in sensors.sensor_ids, f"unknown sensor id {_sid}"
            for _lid in c1.location_ids:
                assert _lid in locations.location_ids, f"unknown location id {_lid}"

        # reference existence in events.json
        for e1 in events.root:
            for _sid in e1.sensor_ids:
                assert _sid in sensors.sensor_ids, f"unknown sensor id {_sid}"

    def get(
        self,
        sensor_id: str,
        from_datetime: datetime.datetime,
        to_datetime: datetime.datetime,
    ) -> list[em27_metadata_types.SensorDataContext]:
        """For a given `sensor_id`, return the list of metadata contexts between
        `from_datetime` and `to_datetime`.

        Each "context" is a time period where the deployment is constant. For example,
        when requesting a full 24 hour day, and the deployment changed at noon, the
        returned list will contain two items: One context until noon, and one
        context after noon.

        Args:
            sensor_id:      The sensor ID.
            from_datetime:  The start of the requested time period.
            to_datetime:    The end of the requested time period.

        Returns:  A list of `SensorDataContext` objects.

        Raises:
            ValueError:      If the `sensor_id` is unknown or the `from_datetime` is
                             greater than the given `to_datetime`."""

        try:
            sensor = next(filter(lambda s: s.sensor_id == sensor_id, self.sensors.root))
        except StopIteration:
            raise ValueError(f"Unknown sensor_id {sensor_id}")

        if from_datetime > to_datetime:
            raise ValueError(f"from_datetime ({from_datetime}) > to_datetime ({to_datetime})")

        # find all relevant deployments

        deployment_spans: list[
            tuple[
                em27_metadata_types.Deployment,
                datetime.datetime,
                datetime.datetime,
            ]
        ] = []
        for deployment in sensor.deployments:
            deployment_span = (
                deployment,
                deployment.from_datetime_parsed,
                deployment.to_datetime_parsed,
            )
            if len(deployment_spans) > 0:
                last_deployment, last_from_datetime, last_to_datetime = deployment_spans[-1]
                if (
                    deployment_span[1] - last_to_datetime
                ).total_seconds() == 1 and last_deployment.model_dump(
                    exclude={"from_datetime", "to_datetime"}
                ) == deployment.model_dump(exclude={"from_datetime", "to_datetime"}):
                    deployment_spans[-1] = (
                        last_deployment,
                        last_from_datetime,
                        deployment_span[2],
                    )
                    continue
            deployment_spans.append(deployment_span)

        relevant_deployments = [
            (
                deployment,
                deployment_from_datetime.astimezone(datetime.timezone.utc),
                deployment_to_datetime.astimezone(datetime.timezone.utc),
            )
            for deployment, deployment_from_datetime, deployment_to_datetime in deployment_spans
            if tum_esm_utils.timing.datetime_span_intersection(
                (from_datetime, to_datetime),
                (deployment_from_datetime, deployment_to_datetime),
            )
            is not None
        ]

        for s1, s2 in zip(relevant_deployments[:-1], relevant_deployments[1:]):
            assert s1[2] < s2[1], f"this should not happen, overlapping deployments: {s1} and {s2}"

        if len(relevant_deployments) == 0:
            return []

        # crop deployments list to requested time period

        first_deployment, first_from_datetime, first_to_datetime = relevant_deployments[0]
        if first_from_datetime < from_datetime:
            relevant_deployments[0] = (first_deployment, from_datetime, first_to_datetime)

        last_deployment, last_from_datetime, last_to_datetime = relevant_deployments[-1]
        if last_to_datetime > to_datetime:
            relevant_deployments[-1] = (last_deployment, last_from_datetime, to_datetime)

        # create sensor data contexts

        sensor_data_contexts: list[em27_metadata_types.SensorDataContext] = []
        for deployment, deployment_from_datetime, deployment_to_datetime in relevant_deployments:
            if deployment_from_datetime >= deployment_to_datetime:
                continue

            location = next(
                filter(
                    lambda l: l.location_id == deployment.location_id,
                    self.locations.root,
                )
            )
            atmospheric_profile_location: em27_metadata_types.LocationMetadata
            if deployment.atmospheric_profile_location_id is not None:
                atmospheric_profile_location = next(
                    filter(
                        lambda l: l.location_id == deployment.atmospheric_profile_location_id,
                        self.locations.root,
                    )
                )
            else:
                atmospheric_profile_location = location

            sensor_data_contexts.append(
                em27_metadata_types.SensorDataContext(
                    sensor_id=sensor.sensor_id,
                    serial_number=sensor.serial_number,
                    from_datetime=deployment_from_datetime,
                    to_datetime=deployment_to_datetime,
                    location=location,
                    utc_offset=deployment.utc_offset,
                    pressure_data_source=(
                        deployment.pressure_data_source
                        if deployment.pressure_data_source
                        else sensor.sensor_id
                    ),
                    atmospheric_profile_location=atmospheric_profile_location,
                )
            )

        return sensor_data_contexts

    def explode_efficiently(
        self,
        sensor_id: str,
        datetimes: list[datetime.datetime],
    ) -> list[
        Optional[
            tuple[
                em27_metadata_types.LocationMetadata,
                float,
                str,
                em27_metadata_types.LocationMetadata,
            ]
        ]
    ]:
        """For a given `sensor_id`, return the list of metadata contexts for each
        datetime in `datetimes`.

        Returns: list[tuple[location, utc_offset, pressure_data_source, atmospheric_profile_location]]"""

        try:
            sensor = next(filter(lambda s: s.sensor_id == sensor_id, self.sensors.root))
        except StopIteration:
            raise ValueError(f"Unknown sensor_id {sensor_id}")

        out: list[
            Optional[
                tuple[
                    em27_metadata_types.LocationMetadata,
                    float,
                    str,
                    em27_metadata_types.LocationMetadata,
                ]
            ]
        ] = []

        current_deployment_index = 0
        for i, dt in enumerate(datetimes):
            # skip all deployments smaller than the current datetime
            while dt > sensor.deployments[current_deployment_index].to_datetime_parsed:
                current_deployment_index += 1
                if current_deployment_index >= len(sensor.deployments):
                    break

            # add nones if the current datetime is larger than the last deployment
            if current_deployment_index >= len(sensor.deployments):
                out.extend([None] * (len(datetimes) - i))
                break

            # add none if the current datetime is smaller than the next deployment
            if dt < sensor.deployments[current_deployment_index].from_datetime_parsed:
                out.append(None)
                continue

            deployment = sensor.deployments[current_deployment_index]
            location = next(
                filter(
                    lambda l: l.location_id == deployment.location_id,
                    self.locations.root,
                )
            )
            atmospheric_profile_location: em27_metadata_types.LocationMetadata
            if deployment.atmospheric_profile_location_id is not None:
                atmospheric_profile_location = next(
                    filter(
                        lambda l: l.location_id == deployment.atmospheric_profile_location_id,
                        self.locations.root,
                    )
                )
            else:
                atmospheric_profile_location = location

            out.append(
                (
                    location,
                    deployment.utc_offset,
                    deployment.pressure_data_source
                    if deployment.pressure_data_source
                    else sensor.sensor_id,
                    atmospheric_profile_location,
                )
            )

        return out

    def get_events(
        self,
        sensor_id: str,
        from_datetime: datetime.datetime,
        to_datetime: datetime.datetime,
    ) -> list[em27_metadata_types.EventMetadata]:
        """For a given `sensor_id`, return the list of events between
        `from_datetime` and `to_datetime`.

        Args:
            sensor_id:      The sensor ID.
            from_datetime:  The start of the requested time period.
            to_datetime:    The end of the requested time period.
        """

        events: list[em27_metadata_types.EventMetadata] = []
        for event in self.events.root:
            if sensor_id in event.sensor_ids:
                if (
                    tum_esm_utils.timing.datetime_span_intersection(
                        (from_datetime, to_datetime),
                        (event.from_datetime_parsed, event.to_datetime_parsed),
                    )
                    is not None
                ):
                    events.append(event.model_copy(deep=True))
        return events
