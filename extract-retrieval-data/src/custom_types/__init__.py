from typing import Literal

Rate = Literal[
    "10 min", "5 min", "2 min", "1 min", "30 sec", "15 sec", "10 sec", "5 sec", "2 sec", "1 sec"
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
