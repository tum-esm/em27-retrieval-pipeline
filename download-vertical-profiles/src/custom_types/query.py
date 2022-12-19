from typing import Any
from pydantic import BaseModel
from .location_data_types import Date


class QueryLocation(BaseModel):
    """A query location, e.g.,
    {
        "lat": 48,
        "lon": 11,
    }.
    """

    lat: int
    lon: int

    class Config:
        frozen = True

    def slug(self, verbose: bool = False) -> str:
        """E.g.,
        48N012E (verbose=False)
        48.00N_12.00E (verbose=True)
        """
        str_ = f"{abs(self.lat):.2f}" if verbose else f"{abs(self.lat):02}"
        str_ += "S" if self.lat < 0 else "N"
        str_ += "_" if verbose else ""
        str_ += f"{abs(self.lon):.2f}" if verbose else f"{abs(self.lon):03}"
        return str_ + ("W" if self.lon < 0 else "E")


class Query(BaseModel):
    """A query, e.g.,
    {
        "from_date": "20210927",
        "to_date": "20211015",
        "query_location": <class 'QueryLocation'>,
    }.
    """

    from_date: Date
    to_date: Date
    location: QueryLocation

    def to_slugged_json(self) -> dict[str, Any]:
        return {
            "location": self.location.slug(),
            "from_date": self.from_date,
            "to_date": self.to_date,
        }
