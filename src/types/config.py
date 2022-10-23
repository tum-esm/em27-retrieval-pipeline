import os, shutil

from pathlib import Path
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, PositiveInt, constr, validator, Extra

PROJECT_DIR = Path(os.path.abspath(__file__)).parents[2]

LOCATION_DATA_PATH = os.path.join(PROJECT_DIR, "location_data")
CONFIG_FILE_PATH = os.path.join(PROJECT_DIR, "config", "config.json")
CONFIG_LOCK_PATH = os.path.join(PROJECT_DIR, "config", ".config.lock")

# NOTE - Mail/HTTP Validator(?)


class Configuration(BaseModel, extra=Extra.forbid):
    user: str
    from_date: date
    to_date: Optional[date] = None
    location_data: constr(regex=r"r^(https://.*)|(git@.*)$")  # type: ignore
    dst_directory: Optional[str] = None
    max_idle_time: PositiveInt = 60

    @validator("from_date", pre=True)
    def parse_from_date(cls, v: str) -> date:
        from_date = datetime.strptime(v, "%Y%m%d").date()
        assert (
            from_date <= datetime.utcnow().date()
        ), f"from_date {from_date} is in the future"
        return from_date

    @validator("to_date", pre=True)
    def parse_to_data(cls, v: Optional[str], **kwargs) -> date:
        if v is not None:
            to_date = datetime.strptime(v, "%Y%m%d").date()
            assert (
                to_date <= datetime.utcnow().date()
            ), f"to_date {to_date} is in the future"
        else:
            to_date = datetime.utcnow().date()
        from_date = kwargs["values"]["from_date"]
        assert from_date <= to_date, f"from_date {from_date} after to_date {to_date}"
        return to_date

    @validator("dst_directory")
    def set_dst_directory(cls, v: Optional[str]) -> str:
        if v is None:
            v = LOCATION_DATA_PATH
        return v  # TODO - PATH / Check if new data
