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
            for l1 in s1.setups:
                assert l1.value.location_id in locations.location_ids, (
                    f"unknown location id {l1.value.location_id}"
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

        Each "context" is a time period where the setup is constant. For example,
        when requesting a full 24 hour day, and the setup changed at noon, the
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

        # find all relevant setups

        setup_spans: list[
            tuple[
                em27_metadata_types.SetupsListItem,
                datetime.datetime,
                datetime.datetime,
            ]
        ] = []
        for setup in sensor.setups:
            setup_span = (
                setup,
                setup.from_datetime_parsed,
                setup.to_datetime_parsed,
            )
            if len(setup_spans) > 0:
                last_setup, last_from_datetime, last_to_datetime = setup_spans[-1]
                if (
                    (setup_span[1] - last_to_datetime).total_seconds() == 1
                    and last_setup.value == setup.value
                ):
                    setup_spans[-1] = (last_setup, last_from_datetime, setup_span[2])
                    continue
            setup_spans.append(setup_span)

        relevant_setups = [
            (
                setup,
                setup_from_datetime.astimezone(datetime.timezone.utc),
                setup_to_datetime.astimezone(datetime.timezone.utc),
            )
            for setup, setup_from_datetime, setup_to_datetime in setup_spans
            if tum_esm_utils.timing.datetime_span_intersection(
                (from_datetime, to_datetime),
                (setup_from_datetime, setup_to_datetime),
            )
            is not None
        ]

        for s1, s2 in zip(relevant_setups[:-1], relevant_setups[1:]):
            assert s1[2] < s2[1], (
                f"this should not happen, overlapping setups: {s1} and {s2}"
            )

        if len(relevant_setups) == 0:
            return []

        # crop setups list to requested time period

        first_setup, first_from_datetime, first_to_datetime = relevant_setups[0]
        if first_from_datetime < from_datetime:
            relevant_setups[0] = (first_setup, from_datetime, first_to_datetime)

        last_setup, last_from_datetime, last_to_datetime = relevant_setups[-1]
        if last_to_datetime > to_datetime:
            relevant_setups[-1] = (last_setup, last_from_datetime, to_datetime)

        # create sensor data contexts

        sensor_data_contexts: list[em27_metadata_types.SensorDataContext] = []
        for setup, setup_from_datetime, setup_to_datetime in relevant_setups:
            if setup_from_datetime >= setup_to_datetime:
                continue

            location = next(
                filter(
                    lambda l: l.location_id == setup.value.location_id,
                    self.locations.root,
                )
            )
            atmospheric_profile_location: em27_metadata_types.LocationMetadata
            if setup.value.atmospheric_profile_location_id is not None:
                atmospheric_profile_location = next(
                    filter(
                        lambda l: l.location_id == setup.value.atmospheric_profile_location_id,
                        self.locations.root,
                    )
                )
            else:
                atmospheric_profile_location = location

            sensor_data_contexts.append(
                em27_metadata_types.SensorDataContext(
                    sensor_id=sensor.sensor_id,
                    serial_number=sensor.serial_number,
                    from_datetime=setup_from_datetime,
                    to_datetime=setup_to_datetime,
                    location=location,
                    utc_offset=setup.value.utc_offset,
                    pressure_data_source=(
                        setup.value.pressure_data_source
                        if setup.value.pressure_data_source
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

        current_setup_index = 0
        for i, dt in enumerate(datetimes):
            # skip all setups smaller than the current datetime
            while dt > sensor.setups[current_setup_index].to_datetime_parsed:
                current_setup_index += 1
                if current_setup_index >= len(sensor.setups):
                    break

            # add nones if the current datetime is larger than the last setup
            if current_setup_index >= len(sensor.setups):
                out.extend([None] * (len(datetimes) - i))
                break

            # add none if the current datetime is smaller than the next setup
            if dt < sensor.setups[current_setup_index].from_datetime_parsed:
                out.append(None)
                continue

            setup = sensor.setups[current_setup_index]
            location = next(
                filter(
                    lambda l: l.location_id == setup.value.location_id,
                    self.locations.root,
                )
            )
            atmospheric_profile_location: em27_metadata_types.LocationMetadata
            if setup.value.atmospheric_profile_location_id is not None:
                atmospheric_profile_location = next(
                    filter(
                        lambda l: l.location_id == setup.value.atmospheric_profile_location_id,
                        self.locations.root,
                    )
                )
            else:
                atmospheric_profile_location = location

            out.append(
                (
                    location,
                    setup.value.utc_offset,
                    setup.value.pressure_data_source
                    if setup.value.pressure_data_source
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
