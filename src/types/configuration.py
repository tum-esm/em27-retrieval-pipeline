import os
import logging
from pathlib import Path
from datetime import date
from datetime import datetime

from attrs import validators as val
from attrs import Attribute, frozen, field

TODAY = datetime.utcnow().date()
PROJECT_DIR = Path(os.path.abspath(__file__)).parents[2]
DST_DIR = os.path.join(PROJECT_DIR, "location_data")

#NOTE - Utils(?)
def _date_converter(value: str | date) -> date:
    match value:
        case date():
            return value
        case str():
            try:
                return datetime.strptime(value, "%Y%m%d").date()
            except ValueError as e:
                raise ValueError(f"Date format must be %Y%m%d") from e
        case _:
            raise TypeError(f"Date must be <class 'str'>")

@frozen
class Configuration:
    email: str = field(
        validator=[val.instance_of(str), val.matches_re(r"[^@]+@[^@]+\.[^@]+")]
    )
    location_data: str = field(
        validator=[val.instance_of(str), val.matches_re(r"(https://.*)|(git@.*)")]
    )

    from_date: date = field(default=TODAY, converter=_date_converter)
    to_date: date = field(default=TODAY, converter=_date_converter)

    dst_directory: str = field(default=DST_DIR, validator=[val.instance_of(str)])
    max_idle_time: int = field(default=60, validator=[val.instance_of(int), val.gt(0)])

    @from_date.validator
    def _(self, _:Attribute, value: date) -> None:
        if value > TODAY:
            raise ValueError(f"Date from_date in the future")

    @to_date.validator
    def _(self, _:Attribute, value: date) -> None:
        if value > TODAY:
            raise ValueError(f"Date to_date in the future")
        if self.from_date > value:
            raise ValueError(f"Date from_date after to_date") 
    
    @dst_directory.validator
    def _(self, _:Attribute, value: str) -> None:
        if not os.path.isdir(value):
            logging.warn(f"Creating empty directory {value}")
            os.makedirs(value)