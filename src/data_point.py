import datetime
from dataclasses import dataclass


@dataclass
class DataPoint:
    date: datetime
    sensor: str
    color: int
