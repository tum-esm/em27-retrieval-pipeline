from typing import Literal
from pydantic import BaseModel
from src.custom_types import Location


class StationInfo(BaseModel):
    """A station's information, e.g.,
    {
        "direction": "north",
        "sensor_serial_number": 61,
        "default_location": <class 'Location'>
    }.
    """

    direction: Literal["north", "east", "south", "west", "center"]
    sensor_serial_number: int
    default_location: Location
