from typing import Callable
from datetime import datetime

Date = str
SensorId = str
LocationId = str
CampaignId = str

dt_to_str: Callable[[datetime], Date] = lambda v: v.strftime("%Y%m%d")
str_to_dt: Callable[[Date], datetime] = lambda v: datetime.strptime(v, "%Y%m%d")

from .campaign import Campaign, CampaignStation
from .location import Location
from .sensor import Sensor, SensorLocation
