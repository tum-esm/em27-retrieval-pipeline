from pydantic import BaseModel


class Location(BaseModel):
    """A station's location, e.g.,
    {
        "location_id": "TUM_G",
        "details": "TUM in Garching",
        "lon": 11.671,
        "lat": 48.261,
        "alt": 491
    }.
    """

    location_id: str
    details: str
    lat: float
    lon: float
    alt: int
