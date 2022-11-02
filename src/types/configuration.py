import os
import logging
from pathlib import Path
from datetime import datetime, date, timedelta

from attrs import validators as val
from attrs import Attribute, frozen, field

TODAY = datetime.utcnow().date()
PROJECT_DIR = Path(os.path.abspath(__file__)).parents[2]
DST_DIR = os.path.join(PROJECT_DIR, "vertical-profiles")


@frozen
class Configuration:
    email: str = field(
        validator=[val.instance_of(str), val.matches_re(r"[^@]+@[^@]+\.[^@]+")]
    )
    location_data: str = field(
        validator=[
            val.instance_of(str),
            val.matches_re(r"(https://raw.githubusercontent.com/.*)"),
        ]
    )
    git_username: str = field(validator=val.instance_of(str))
    git_token: str = field(validator=val.instance_of(str))
    from_date: str = field(default="", validator=val.instance_of(str))
    to_date: str = field(default=(TODAY-timedelta(5)).strftime("%Y%m%d"), validator=val.instance_of(str))
    dst_directory: str = field(default=DST_DIR, validator=val.instance_of(str))
    max_idle_time: int = field(default=60, validator=[val.instance_of(int), val.gt(0)])

    @from_date.validator
    def _(self, _: Attribute, value: str) -> None:
        if value != "": 
            try:
                date = datetime.strptime(value, "%Y%m%d").date()
                if (TODAY - date).days < 5:
                    raise ValueError(f"Date from_date too recent or in the future")
            except ValueError as e:
                raise ValueError(f"Date from_date must be %Y%m%d") from e

    @to_date.validator
    def _(self, _: Attribute, value: str) -> None:
        try:
            date = datetime.strptime(value, "%Y%m%d").date()
            if (TODAY - date).days < 5:
                raise ValueError(f"Date to_date too recent or in the future")
        except ValueError as e:
            raise ValueError(f"Date to_date must be %Y%m%d") from e
        if self.from_date > value:
            raise ValueError(f"Date from_date after to_date")

    @dst_directory.validator
    def _(self, _: Attribute, value: str) -> None:
        if not os.path.isdir(value):
            logging.info(f"Creating empty directory {value}")
            os.makedirs(value)
