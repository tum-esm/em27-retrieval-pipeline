from attrs import frozen


@frozen
class Location:
    details: str
    lon: float
    lat: float
    alt: int