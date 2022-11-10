from attrs import frozen


@frozen
class Location:
    """A location's data, e.g., "BRU":
    {
        "details": "Industriegelände an der Brudermühlstraße",
        "lon": 11.547,
        "lat": 48.111,
        "alt": 528
    }.
    """
    details: str
    lon: float
    lat: float
    alt: int