from pydantic import BaseModel, validator
from typing import Literal
from .validators import validate_float, validate_int, validate_str


class Location(BaseModel):
    location_id: str
    details: str
    lon: float
    lat: float
    alt: float

    # validators
    _val_location_id = validator("location_id", pre=True, allow_reuse=True)(
        validate_str(min_len=1, max_len=64, regex="^[A-Z0-9_]+$"),
    )
    _val_details = validator("details", pre=True, allow_reuse=True)(
        validate_str(min_len=3),
    )
    _val_lon = validator("lon", pre=True, allow_reuse=True)(
        validate_float(minimum=-180, maximum=180),
    )
    _val_lat = validator("lat", pre=True, allow_reuse=True)(
        validate_float(minimum=-90, maximum=90),
    )
    _val_alt = validator("alt", pre=True, allow_reuse=True)(
        validate_float(minimum=-20, maximum=10000),
    )


class SensorUTCOffset(BaseModel):
    from_date: str
    to_date: str
    utc_offset: float

    # validators
    _val_date_string = validator(*["from_date", "to_date"], pre=True, allow_reuse=True,)(
        validate_str(is_date_string=True),
    )
    _val_utc_offset = validator("utc_offset", pre=True, allow_reuse=True)(
        validate_float(minimum=-12, maximum=12),
    )


class SensorPressureCalibrationFactor(BaseModel):
    from_date: str
    to_date: str
    factor: float

    # validators
    _val_date_string = validator(*["from_date", "to_date"], pre=True, allow_reuse=True,)(
        validate_str(is_date_string=True),
    )
    _val_factor = validator("factor", pre=True, allow_reuse=True)(
        validate_float(minimum=0.1, maximum=10),
    )


class SensorLocation(BaseModel):
    from_date: str
    to_date: str
    location_id: str

    # validators
    _val_date_string = validator(*["from_date", "to_date"], pre=True, allow_reuse=True,)(
        validate_str(is_date_string=True),
    )
    _val_location_id = validator("location_id", pre=True, allow_reuse=True)(
        validate_str(),
    )


class Sensor(BaseModel):
    sensor_id: str
    serial_number: int
    utc_offsets: list[SensorUTCOffset]
    pressure_calibration_factors: list[SensorPressureCalibrationFactor]
    locations: list[SensorLocation]

    # validators
    _val_sensor_id = validator("sensor_id", pre=True, allow_reuse=True)(
        validate_str(min_len=1, max_len=64, regex="^[a-z0-9_]+$"),
    )
    _val_serial_number = validator("serial_number", pre=True, allow_reuse=True)(
        validate_int(minimum=1),
    )


class CampaignStation(BaseModel):
    sensor_id: str
    default_location_id: str
    direction: Literal["north", "east", "south", "west", "center"]

    # validators
    _val_str = validator(
        *["sensor_id", "default_location_id"],
        pre=True,
        allow_reuse=True,
    )(
        validate_str(),
    )


class Campaign(BaseModel):
    campaign_id: str
    from_date: str
    to_date: str
    stations: list[CampaignStation]

    # validators
    _val_campaign_id = validator("campaign_id", pre=True, allow_reuse=True)(
        validate_str(min_len=1, max_len=64, regex="^[a-z0-9_]+$"),
    )
    _val_date_string = validator(*["from_date", "to_date"], pre=True, allow_reuse=True,)(
        validate_str(is_date_string=True),
    )


class SensorDataContext(BaseModel):
    sensor_id: str
    serial_number: int
    utc_offset: float
    pressure_calibration_factor: float
    date: str
    location: Location
