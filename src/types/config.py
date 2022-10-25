import os
import warnings
from pathlib import Path
from typing import ClassVar, Callable

from datetime import date
from datetime import datetime

from attrs import frozen, field
from attrs import validators as val

TODAY = datetime.utcnow().date()
PROJECT_DIR = Path(os.path.abspath(__file__)).parents[2]
DST_DIR = os.path.join(PROJECT_DIR, "location_data")


def date_converter(value: str | date) -> date:
    match value:
        case date():
            return value
        case str():
            try:
                return datetime.strptime(value, "%Y%m%d").date()
            except ValueError as e:
                raise ValueError(f"date {value} must be %Y%m%d") from e
        case _:
            raise TypeError(f"date must be <class 'str'>")


@frozen
class Configuration:
    email: str = field(
        validator=[val.instance_of(str), val.matches_re(r"[^@]+@[^@]+\.[^@]+")]
    )
    location_data: str = field(
        validator=[val.instance_of(str), val.matches_re(r"(https://.*)|(git@.*)")]
    )

    from_date: date = field(default=TODAY, converter=date_converter)
    to_date: date = field(default=TODAY, converter=date_converter)

    dst_directory: str = field(default=DST_DIR, validator=val.instance_of(str))
    max_idle_time: int = field(default=60, validator=[val.instance_of(int), val.gt(0)])

    @from_date.validator
    def _(self, _, value: date) -> None:
        if value > TODAY:
            raise ValueError(f"date {value} in the future")

    @to_date.validator
    def _(self, _, value: date) -> None:
        if value > TODAY:
            raise ValueError(f"date {value} in the future")
        if value < self.from_date:
            raise ValueError(f"to_date < from_date")

    @dst_directory.validator
    def _(self, _, value):
        if not os.path.isdir(value):
            warnings.warn(f"creating empty directory {value}")
            os.makedirs(value)
