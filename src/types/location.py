from attrs import frozen

@frozen
class Location:
    """Example
    details: "..."
    lat: 48.111
    lon: 11.547
    alt: 528
    """
    details: str
    lat: float
    lon: float
    alt: int
