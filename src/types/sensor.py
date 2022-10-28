from datetime import date
from attrs import frozen, field

from src.utils import str_to_date


@frozen
class Sensor:
    from_date: date = field(converter=str_to_date)
    to_date: date = field(converter=str_to_date)
    location: str
