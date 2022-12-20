from typing import Literal
from .query import QueryLocation, Query

Version = Literal["GGG2014", "GGG2020"]

from .config import (
    Config,
    RequestConfig,
    FTPConfig,
    GitHubConfig,
)

from .location_data_types import (
    Date,
    SensorId,
    LocationId,
    Location,
    Sensor,
    SensorLocation,
    dt_to_str,
    str_to_dt,
)
