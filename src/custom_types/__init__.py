import datetime


def dt_to_str(v: datetime.datetime | datetime.date) -> str:
    return v.strftime("%Y%m%d")


def str_to_dt(v: str) -> datetime.datetime:
    return datetime.datetime.strptime(v, "%Y%m%d")


from .config import Config

from .proffast import (
    InputWarning,
    InputWarningsList,
    PylotContainer,
    PylotSession,
)

from .profiles import DownloadQuery
