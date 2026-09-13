from __future__ import annotations

import datetime
import re
from typing import Any, Optional, TypeGuard, cast

import pydantic

_DATETIME_STRING_PATTERN = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{4})$"
_DATETIME_ADAPTER = pydantic.TypeAdapter(datetime.datetime)


def _is_string_keyed_dict(value: object) -> TypeGuard[dict[str, object]]:
    if not isinstance(value, dict):
        return False
    object_dict = cast(dict[object, object], value)
    return all(isinstance(key, str) for key in object_dict)


class TimeSeriesElement(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)

    from_datetime: str = pydantic.Field(
        ...,
        pattern=_DATETIME_STRING_PATTERN,
        description="Datetime in format `YYYY-MM-DDTHH:MM:SSZ` or `YYYY-MM-DDTHH:MM:SS[+-]HHMM`.",
        validation_alias=pydantic.AliasChoices("from_datetime", "from_dt"),
    )
    to_datetime: str = pydantic.Field(
        ...,
        pattern=_DATETIME_STRING_PATTERN,
        description="Datetime in format `YYYY-MM-DDTHH:MM:SSZ` or `YYYY-MM-DDTHH:MM:SS[+-]HHMM`.",
        validation_alias=pydantic.AliasChoices("to_datetime", "to_dt"),
    )

    @pydantic.field_validator("from_datetime", "to_datetime", mode="before")
    @classmethod
    def normalize_legacy_datetime(cls, value: object) -> object:
        if isinstance(value, datetime.datetime):
            parsed = value
        elif isinstance(value, str):
            if cls.matches_datetime_regex(value):
                return value
            try:
                parsed = _DATETIME_ADAPTER.validate_python(value)
            except pydantic.ValidationError:
                return value
        else:
            return value
        if parsed.tzinfo is None:
            # The former library serialized naive datetime values as UTC.
            parsed = parsed.replace(tzinfo=datetime.timezone.utc)
        return parsed.strftime("%Y-%m-%dT%H:%M:%S%z")

    @staticmethod
    def matches_datetime_regex(v: str) -> bool:
        return re.match(_DATETIME_STRING_PATTERN, v) is not None

    @property
    def from_datetime_parsed(self) -> datetime.datetime:
        return datetime.datetime.strptime(self.from_datetime, "%Y-%m-%dT%H:%M:%S%z")

    @property
    def to_datetime_parsed(self) -> datetime.datetime:
        return datetime.datetime.strptime(self.to_datetime, "%Y-%m-%dT%H:%M:%S%z")

    @pydantic.model_validator(mode="after")
    def model_validator(self) -> TimeSeriesElement:
        if self.from_datetime_parsed > self.to_datetime_parsed:
            raise ValueError(
                f"from_datetime ({self.from_datetime}) > to_datetime ({self.to_datetime})"
            )
        if self.from_datetime_parsed.second != 0:
            raise ValueError("from_datetime must be at the beginning of a minute (second=0)")
        if self.to_datetime_parsed.second != 59:
            raise ValueError("to_datetime must be at the end of a minute (second=59)")
        return self


class Deployment(TimeSeriesElement):
    """A sensor deployment that applies during a specific time range."""

    @pydantic.model_validator(mode="before")
    @classmethod
    def flatten_legacy_value(cls, data: object) -> object:
        """Accept the former ``{from_dt, to_dt, value: {...}}`` shape."""
        if not _is_string_keyed_dict(data):
            return data

        legacy_value: object = data.get("value", data.get("v"))
        if isinstance(legacy_value, pydantic.BaseModel):
            legacy_value = legacy_value.model_dump()
        if not _is_string_keyed_dict(legacy_value):
            return data

        flattened: dict[str, object] = dict(legacy_value)
        flattened.update({key: value for key, value in data.items() if key not in {"value", "v"}})
        return flattened

    location_id: str = pydantic.Field(
        ...,
        min_length=1,
        description="Location ID referring to a location named in `locations.json`",
        validation_alias=pydantic.AliasChoices("location_id", "lid"),
    )
    pressure_data_source: Optional[str] = pydantic.Field(
        default=None,
        min_length=1,
        description="Pressure data source, if not set, using the pressure of the sensor",
        validation_alias=pydantic.AliasChoices("pressure_data_source", "pds"),
    )
    utc_offset: float = pydantic.Field(
        default=0,
        gt=-12,
        lt=12,
        description="UTC offset of the location, if not set, using an offset of 0",
    )
    atmospheric_profile_location_id: Optional[str] = pydantic.Field(
        default=None,
        min_length=1,
        description="Location ID referring to a location named in `locations.json`. This location's coordinates are used for the atmospheric profiles in the retrieval.",
        validation_alias=pydantic.AliasChoices("atmospheric_profile_location_id", "profile_lid"),
    )

    @property
    def value(self) -> Deployment:
        """Return this deployment for compatibility with the former nested model."""
        return self


# Former names parse directly into the canonical deployment model.
Setup = Deployment
SetupsListItem = Deployment


class LocationMetadata(pydantic.BaseModel):
    """Definition of a measurement location at which an EM27/SUN was positioned."""

    location_id: str = pydantic.Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description=(
            "Your internal location ID identifying a specific location. "
            + "Allowed values: letters, numbers, dashes, underscores."
        ),
    )
    details: str = pydantic.Field("", min_length=0)
    lon: float = pydantic.Field(..., ge=-180, le=180)
    lat: float = pydantic.Field(..., ge=-90, le=90)
    alt_asl: float = pydantic.Field(
        ...,
        ge=-20,
        le=10000,
        validation_alias=pydantic.AliasChoices("alt_asl", "alt"),
    )


class LocationMetadataList(pydantic.RootModel[list[LocationMetadata]]):
    root: list[LocationMetadata]

    @property
    def location_ids(self: LocationMetadataList) -> list[str]:
        return [_l.location_id for _l in self.root]

    @pydantic.model_validator(mode="after")
    def check_id_uniqueness(self: LocationMetadataList) -> LocationMetadataList:
        for location_id in self.location_ids:
            if self.location_ids.count(location_id) > 1:
                raise ValueError(f"Location ID {location_id} is not unique")
        return self


class SensorMetadata(pydantic.BaseModel):
    """Metadata for a single sensor. Where has an EM27/SUN instrument been deployed over the years? Which UTC offsets did it record data in? For each deployment, should we use the atmospheric profiles from a different location or the pressure data from a different source?"""

    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)
    sensor_id: str = pydantic.Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description=(
            "Your internal sensor ID identifying a specific EM27/SUN (system). "
            + "Allowed characters: letters, numbers, dashes, underscores."
        ),
    )
    serial_number: int = pydantic.Field(
        ...,
        ge=1,
        description="Serial number of the EM27/SUN",
    )
    deployments: list[Deployment] = pydantic.Field(
        ...,
        min_length=0,
        validation_alias=pydantic.AliasChoices("deployments", "setups"),
    )
    calibration_factors: list[Any] = pydantic.Field(
        default=[],
        deprecated=(
            "This field has been deprecated. Every Research group has their "
            + "own strategy of calibrating their data, hence, we don't want to "
            + "propose any standard with this. Also, EM27/SUN calibration is more "
            + "complex than just multiplying a factor to the data."
        ),
        exclude=True,
    )

    @pydantic.model_validator(mode="after")
    def check_timeseries_integrity(self: SensorMetadata) -> SensorMetadata:
        times: list[datetime.datetime] = []
        for deployment in self.deployments:
            times.append(deployment.from_datetime_parsed)
            times.append(deployment.to_datetime_parsed)
        for t1, t2 in zip(times[:-1], times[1:]):
            if t2 <= t1:
                raise ValueError(f"Deployments timeseries are overlapping or unsorted: {t1} > {t2}")
        return self

    @property
    def setups(self) -> list[Deployment]:
        """Return deployments for compatibility with the former field name."""
        return self.deployments


class SensorMetadataList(pydantic.RootModel[list[SensorMetadata]]):
    root: list[SensorMetadata]

    @property
    def sensor_ids(self: SensorMetadataList) -> list[str]:
        return [_l.sensor_id for _l in self.root]

    @pydantic.model_validator(mode="after")
    def check_id_uniqueness(self: SensorMetadataList) -> SensorMetadataList:
        for sensor_id in self.sensor_ids:
            if self.sensor_ids.count(sensor_id) > 1:
                raise ValueError(f"Sensor ID {sensor_id} is not unique")
        return self


class CampaignMetadata(TimeSeriesElement):
    """Can be used to group measurements together, e.g. "Hamburg Campaign". The campaigns will be included in the dataset bundles in the column `campaign_ids`."""

    campaign_id: str = pydantic.Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description=(
            "Your internal sensor ID identifying a specific campaign. "
            + "Allowed values: letters, numbers, dashes, underscores."
        ),
    )
    sensor_ids: list[str]
    location_ids: list[str]


class CampaignMetadataList(pydantic.RootModel[list[CampaignMetadata]]):
    root: list[CampaignMetadata] = []

    @property
    def campaign_ids(self: CampaignMetadataList) -> list[str]:
        return [_l.campaign_id for _l in self.root]

    @pydantic.model_validator(mode="after")
    def check_id_uniqueness(self: CampaignMetadataList) -> CampaignMetadataList:
        for campaign_id in self.campaign_ids:
            if self.campaign_ids.count(campaign_id) > 1:
                raise ValueError(f"Campaign ID {campaign_id} is not unique")
        return self


class EventMetadata(TimeSeriesElement):
    """Can be used to mark special events during measurements, e.g. "Testing New Solar Tracker". You can mark that the data during an event should not be used in downstream tasks. The dataset bundles will include the columns `event_description` and `event_data_quality_flag` (0 = good data, 1 = should not be used because of an event)."""

    sensor_ids: list[str] = pydantic.Field(
        ...,
        min_length=1,
        description="List of sensor IDs involved in the event",
    )
    description: str = pydantic.Field(
        ...,
        min_length=1,
        description="Description of the event",
    )
    data_is_usable: bool = pydantic.Field(
        ...,
        description="Indicates if the data recorded during the event is usable for downstream analysis",
    )


class EventMetadataList(pydantic.RootModel[list[EventMetadata]]):
    root: list[EventMetadata]


class EM27MetadataObject(pydantic.BaseModel):
    sensors: SensorMetadataList
    locations: LocationMetadataList
    campaigns: CampaignMetadataList = pydantic.Field(default=CampaignMetadataList(root=[]))
    events: EventMetadataList = pydantic.Field(default=EventMetadataList(root=[]))


class SensorDataContext(pydantic.BaseModel):
    sensor_id: str
    serial_number: int
    from_datetime: datetime.datetime
    to_datetime: datetime.datetime
    location: LocationMetadata

    # set to default values if not specified
    utc_offset: float
    pressure_data_source: str
    calibration_factors: Any = pydantic.Field(
        default=None,
        deprecated=(
            "This field has been deprecated. Every Research group has their "
            + "own strategy of calibrating their data, hence, we don't want to "
            + "propose any standard with this. Also it calibration is more "
            + "complex than just multiplying a factor to the data."
        ),
        exclude=True,
    )
    atmospheric_profile_location: LocationMetadata

    @pydantic.field_serializer("from_datetime", "to_datetime")
    def t_serializer(self, dt: datetime.datetime, _info: Any) -> str:
        return dt.strftime("%Y-%m-%dT%H:%M:%S%z")
