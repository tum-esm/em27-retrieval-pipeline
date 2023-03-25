from typing import Any
from pydantic import BaseModel


class DownloadQueryLocation(BaseModel):
    """Pydantic model:

    ```python
    lat: int
    lon: int
    ```
    """

    lat: int
    lon: int

    class Config:
        frozen = True

    def slug(self, verbose: bool = False) -> str:
        """Return a slug for the location

        verbose = false: `48N011E``
        verbose = true: `48.00N_11.00E`
        """

        str_ = f"{abs(self.lat):.2f}" if verbose else f"{abs(self.lat):02}"
        str_ += "S" if self.lat < 0 else "N"
        str_ += "_" if verbose else ""
        str_ += f"{abs(self.lon):.2f}" if verbose else f"{abs(self.lon):03}"
        return str_ + ("W" if self.lon < 0 else "E")


class DownloadQuery(BaseModel):
    """Pydantic model:

    ```python
    from_date: str
    to_date: str
    location: QueryLocation
    ```
    """

    from_date: str
    to_date: str
    location: DownloadQueryLocation

    def to_slugged_json(self) -> dict[str, Any]:
        return {
            "location": self.location.slug(),
            "from_date": self.from_date,
            "to_date": self.to_date,
        }
