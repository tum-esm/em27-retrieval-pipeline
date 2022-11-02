from typing import Callable
from datetime import date
from datetime import datetime
from attrs import field, define

str_to_date: Callable[[str], date] = lambda s: datetime.strptime(s, "%Y%m%d").date()

@define(on_setattr=False) # type: ignore
class Query:
    coordinates: str
    from_date: date = field(converter=str_to_date) # type: ignore
    to_date: date = field(converter=str_to_date) # type: ignore
    