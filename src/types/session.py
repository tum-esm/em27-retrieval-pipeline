import pydantic
from typing import TypedDict


class SessionDict(TypedDict):
    sensor: str
    location: str
    date: str
    lat: float
    lon: float
    alt: int
    serial_number: int
