from datetime import datetime
from typing import Callable


dt_to_str: Callable[[datetime], str] = lambda v: v.strftime("%Y%m%d")
str_to_dt: Callable[[str], datetime] = lambda v: datetime.strptime(v, "%Y%m%d")

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
