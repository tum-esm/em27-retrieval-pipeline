from typing import Literal
from pydantic import BaseModel


class CampaignStation(BaseModel):
    """A campaign's station, e.g.,
    {
        "sensor": "ma",
        "default_location": "HAW",
        "direction": "east"
    }.
    """

    sensor: str
    default_location: str
    direction: Literal["north", "east", "south", "west", "center"]


class Campaign(BaseModel):
    """A campaign, e.g., "hamburg":
    {
        "from_date": "20220524",
        "to_date": "20270715",
        "stations": [CampaignStation, ...]
    }.
    """

    from_date: str
    to_date: str
    stations: list[CampaignStation]
