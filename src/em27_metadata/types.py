from __future__ import annotations
from typing import Any, Optional
import datetime
import re
import pydantic


class TimeSeriesElement(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)

    from_datetime: datetime.datetime = pydantic.Field(
        ..., validation_alias=pydantic.AliasChoices("from_datetime", "from_dt")
    )
    to_datetime: datetime.datetime = pydantic.Field(
        ..., validation_alias=pydantic.AliasChoices("to_datetime", "to_dt")
    )

    @pydantic.field_validator("from_datetime", "to_datetime", mode="before")
    def datetime_string_validator(cls, v: str | datetime.datetime) -> datetime.datetime:
        if isinstance(v, datetime.datetime):
            return v
        assert isinstance(v, str), "must be a string"
        assert TimeSeriesElement.matches_datetime_regex(v), (
            "must match the pattern YYYY-MM-DDTHH:MM:SS+HHMM"
        )
        return datetime.datetime.strptime(v, "%Y-%m-%dT%H:%M:%S%z")

    @staticmethod
    def matches_datetime_regex(v: str) -> bool:
        return (
            re.match(r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})([\+\-])(\d{4})$", v)
            is not None
        )

    @pydantic.model_validator(mode="after")
    def model_validator(self) -> TimeSeriesElement:
        if self.from_datetime > self.to_datetime:
            raise ValueError(
                f"from_datetime ({self.from_datetime}) > to_datetime ({self.to_datetime})"
            )
        if self.from_datetime.second != 0:
            raise ValueError("from_datetime must be at the beginning of a minute (second=0)")
        if self.to_datetime.second != 59:
            raise ValueError("to_datetime must be at the end of a minute (second=59)")
        return self

    @pydantic.field_serializer("from_datetime", "to_datetime")
    def t_serializer(self, dt: datetime.date, _info: Any) -> str:
        return dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")


class Setup(pydantic.BaseModel):
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


class SetupsListItem(TimeSeriesElement):
    """An element in the `sensor.setups` list"""

    value: Setup = pydantic.Field(..., validation_alias=pydantic.AliasChoices("value", "v"))


class LocationMetadata(pydantic.BaseModel):
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
    alt: float = pydantic.Field(..., ge=-20, le=10000)


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
    """Metadata for a single sensor."""

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
    setups: list[SetupsListItem] = pydantic.Field(
        ...,
        min_length=0,
    )
    calibration_factors: list[Any] = pydantic.Field(
        default=[],
        deprecated=(
            "This field has been deprecated. Every Research group has their "
            + "own strategy of calibrating their data, hence, we don't want to "
            + "propose any standard with this. Also it calibration is more "
            + "complex than just multiplying a factor to the data."
        ),
        exclude=True,
    )

    @pydantic.model_validator(mode="after")
    def check_timeseries_integrity(self: SensorMetadata) -> SensorMetadata:
        times: list[datetime.datetime] = []
        for s in self.setups:
            times.append(s.from_datetime)
            times.append(s.to_datetime)
        for t1, t2 in zip(times[:-1], times[1:]):
            if t2 <= t1:
                raise ValueError(f"Setups timeseries are overlapping or unsorted: {t1} > {t2}")
        return self


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
    def t_serializer(self, dt: datetime.date, _info: Any) -> str:
        return dt.strftime("%Y-%m-%dT%H:%M:%S%z")
