from pydantic import BaseModel


class Location(BaseModel):
    """A location, e.g., "BRU":
    {
        "details": "Industriegelände an der Brudermühlstraße",
        "lon": 11.547,
        "lat": 48.111,
        "alt": 528
    }.
    """

    details: str
    lat: float
    lon: float
    alt: float
