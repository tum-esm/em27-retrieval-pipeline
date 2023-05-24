from typing import Any
from ..validators import apply_field_validators
import pydantic


class DownloadQueryLocation(pydantic.BaseModel):
    """Pydantic model:

    ```python
    lat: int
    lon: int
    ```
    """

    lat: int = pydantic.Field(..., ge=-90, le=90)
    lon: int = pydantic.Field(..., ge=-180, le=180)

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


class DownloadQuery(pydantic.BaseModel):
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

    # validators
    _1 = apply_field_validators(
        ["from_date", "to_date"],
        is_date_string=True,
    )

    def to_slugged_json(self) -> dict[str, Any]:
        return {
            "location": self.location.slug(),
            "from_date": self.from_date,
            "to_date": self.to_date,
        }
