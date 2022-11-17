import os
import logging
from typing import Any
from pathlib import Path
from datetime import datetime, date, timedelta

from attrs import validators as val
from attrs import converters as conv
from attrs import frozen, field

TODAY = datetime.utcnow().date()
PROJECT_DIR = Path(os.path.abspath(__file__)).parents[2]
DST_DIR = os.path.join(PROJECT_DIR, "vertical-profiles")


def str_to_date(value: str | date) -> date:
    """Converts a string to datetime.date."""
    match value:
        case str():
            try:
                return datetime.strptime(value, "%Y%m%d").date()
            except ValueError as e:
                raise ValueError(f"Date format must be %Y%m%d") from e
        case _:
            raise TypeError(f"Date must be <class 'str'>")


@frozen
class Configuration:
    """Validates and represents the user's configuration.

    Configuration
    * email: email granting access to ccycle.gps.caltech.edu ,
    * locationData: GitHub directory containing 'locations.json' and 'sensors.json' ,
    * gitUsername and gitToken: GitHub username and GitHub personal access token ,
    * from_date: start date in _YYYYMMDD_ format; defaults to '00010101' ,
    * to_date: end date in _YYYYMMDD_ format; defaults to five days prior to current date ,
    * dstDirectory: output directory; defaults to 'vertical-profiles' ,
    """

    email: str = field(validator=[val.instance_of(str), val.matches_re(r"[^@]+@[^@]+\.[^@]+")])
    location_data: str = field(
        validator=[
            val.instance_of(str),
            val.matches_re(r"(https://raw.githubusercontent.com/.*)"),
        ]
    )
    git_username: str = field(validator=val.instance_of(str))
    git_token: str = field(validator=val.instance_of(str))
    from_date: date = field(
        default=None,
        converter=conv.pipe(  # type: ignore
            conv.optional(str_to_date),
            conv.default_if_none(date(1, 1, 1)),
        ),
    )
    to_date: date = field(
        default=None,
        converter=conv.pipe(  # type: ignore
            conv.optional(str_to_date),
            conv.default_if_none(TODAY - timedelta(5)),
        ),
    )
    dst_directory: str = field(default=DST_DIR, validator=val.instance_of(str))
    max_idle_time: int = field(default=60, validator=[val.instance_of(int), val.gt(0)])

    @from_date.validator
    def _(self, _: Any, value: date) -> None:
        if (TODAY - value).days < 5:
            raise ValueError(f"Date from_date too recent or in the future")

    @to_date.validator
    def _(self, _: Any, value: date) -> None:
        if (TODAY - value).days < 5:
            raise ValueError(f"Date to_date too recent or in the future")
        if self.from_date > value:
            raise ValueError(f"Date from_date after to_date")

    @dst_directory.validator
    def _(self, _: Any, value: str) -> None:
        if not os.path.isdir(value):
            logging.info(f"Creating empty directory {value}")
            os.makedirs(value)
