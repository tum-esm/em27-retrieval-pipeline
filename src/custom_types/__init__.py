from datetime import datetime


def dt_to_str(v: datetime) -> str:
    return v.strftime("%Y%m%d")


def str_to_dt(v: str) -> datetime:
    return datetime.strptime(v, "%Y%m%d")


from .config import Config

from .automated_proffast import (
    InputWarning,
    InputWarningsList,
    ManualQueueItem,
    ManualQueue,
    PylotContainer,
    PylotSession,
)

from .vertical_profiles import (
    DownloadQueryLocation,
    DownloadQuery,
)
