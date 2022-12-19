from pydantic import BaseModel


class Location(BaseModel):
    """A location, e.g., "TUM_G":
    {
        "details": "TUM in Garching",
        "lon": 11.671,
        "lat": 48.261,
        "alt": 491
    }.
    """

    details: str
    lat: float
    lon: float
    alt: int
