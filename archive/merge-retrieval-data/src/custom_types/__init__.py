from typing import Literal

Rate = Literal[
    "10m", "5m", "2m", "1m", "30s", "15s", "10s", "5s", "2s", "1s"
]


DataType = Literal[
    "gnd_p",
    "gnd_t",
    "app_sza",
    "azimuth",
    "xh2o",
    "xair",
    "xco2",
    "xch4",
    "xco",
    "xch4_s5p",
]


from .config import (
    Config,
    RequestConfig,
    DatabaseConfig,
    GitHubConfig,
)

from .location_data_types import (
    Date,
    SensorId,
    CampaignId,
    LocationId,
    Campaign,
    CampaignStation,
    Location,
    Sensor,
    SensorLocation,
    str_to_dt,
    dt_to_str,
)
