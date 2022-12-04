from typing import Literal
from pydantic import BaseModel


StationId = str


class CampaignStation(BaseModel):
    station_id: StationId
    default_location: str
    direction: Literal["north", "east", "south", "west", "center"]
    lat: float
    lon: float
