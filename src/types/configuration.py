import os
import logging
from pathlib import Path
from datetime import date
from datetime import datetime

from attrs import validators as val
from attrs import Attribute, frozen, field

from src.utils import str_to_date

TODAY = datetime.utcnow().date()
PROJECT_DIR = Path(os.path.abspath(__file__)).parents[2]
DST_DIR = os.path.join(PROJECT_DIR, "vertical-profiles")


@frozen
class Configuration:
    email: str = field(
        validator=[val.instance_of(str), val.matches_re(r"[^@]+@[^@]+\.[^@]+")]
    )
    location_data: str = field(
        validator=[val.instance_of(str), val.matches_re(r"(https://.*)|(git@.*)")]
    )

    git_username: str = field(validator=val.instance_of(str))
    git_token: str = field(validator=val.instance_of(str))

    from_date: date = field(default=TODAY, converter=str_to_date)
    to_date: date = field(default=TODAY, converter=str_to_date)

    dst_directory: str = field(default=DST_DIR, validator=[val.instance_of(str)])
    max_idle_time: int = field(default=60, validator=[val.instance_of(int), val.gt(0)])

    @from_date.validator
    def _(self, _: Attribute, value: date) -> None:
        if value > TODAY:
            raise ValueError(f"Date from_date in the future")

    @to_date.validator
    def _(self, _: Attribute, value: date) -> None:
        if value > TODAY:
            raise ValueError(f"Date to_date in the future")
        if self.from_date > value:
            raise ValueError(f"Date from_date after to_date")

    @dst_directory.validator
    def _(self, _: Attribute, value: str) -> None:
        if not os.path.isdir(value):
            logging.info(f"Creating empty directory {value}")
            os.makedirs(value)
