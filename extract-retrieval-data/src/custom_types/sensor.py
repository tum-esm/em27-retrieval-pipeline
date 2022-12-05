from typing import Literal
from pydantic import BaseModel


class UTCOffset(BaseModel):
    """A sensor's UTC offset, e.g.,
    {
        "from_date": "20220624",
        "to_date": "20220926",
        "utc_offset": 2
    }.
    """

    from_date: str
    to_date: str
    utc_offset: int


class SensorLocation(BaseModel):
    """A sensor's location, e.g.,
    {
        "from_date": "20160927",
        "to_date": "20170705",
        "location": "BRU"
    }.
    """

    from_date: str
    to_date: str
    location: str


class Sensor(BaseModel):
    """A sensor, e.g., "ma":
    {
        "serial_number": 61,
        "utc_offsets": [UTCOffest, ...],
        "locations": [SensorLocation, ...],
    }.
    """

    serial_number: int
    utc_offsets: list[UTCOffset]
    locations: list[SensorLocation]
