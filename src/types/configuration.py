import os
from typing import Any
from pathlib import Path
from datetime import datetime, date

from attrs import validators as val
from attrs import frozen, field

TODAY = datetime.utcnow().date()
PROJECT_PATH = Path(os.path.abspath(__file__)).parents[2]


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
    * location_data: GitHub directory containing 'locations.json' and 'sensors.json' ,
    * git_username and gitToken: GitHub username and GitHub personal access token ,
    * from_date: start date in YYYYMMDD format; defaults to '00010101' ,
    * to_date: end date in YYYYMMDD format; defaults to datetime.utcnow() ,
    * dst_directory: output directory; defaults to 'PROJECT_PATH/vertical_profiles' ,
    * max_await_2014: wall time awaiting GGG2014 data until abortion in seconds; defaults to 600
    * max_await_2020: wall time awaiting GGG2020 data until abortion in seconds; defaults to 10_000
    * max_delay: maximum days of data lag; defaults to 7
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
    from_date: date = field(default="00010101", converter=str_to_date)  # type: ignore
    to_date: date = field(default=datetime.strftime(TODAY, "%Y%m%d"), converter=str_to_date)  # type: ignore
    dst_directory: str = field(
        default=os.path.join(PROJECT_PATH, "vertical_profiles"), validator=val.instance_of(str)
    )
    max_await_2014: int = field(default=600, validator=[val.instance_of(int), val.gt(0)])
    max_await_2020: int = field(default=10_000, validator=[val.instance_of(int), val.gt(0)])
    max_delay: int = field(default=7, validator=[val.instance_of(int), val.ge(0)])

    @from_date.validator
    def _(self, _: Any, value: date) -> None:
        if value > TODAY:
            raise ValueError(f"Date from_date in the future")

    @to_date.validator
    def _(self, _: Any, value: date) -> None:
        if value > TODAY:
            raise ValueError(f"Date to_date in the future")
        if self.from_date > value:
            raise ValueError(f"Date from_date after to_date")
