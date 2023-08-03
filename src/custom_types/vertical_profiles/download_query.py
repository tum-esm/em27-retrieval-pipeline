from __future__ import annotations
import pendulum
import pydantic


class DownloadQuery(pydantic.BaseModel):
    """Pydantic model:

    ```python
    lat: int
    lon: int
    start_date: pendulum.Date
    end_date: pendulum.Date
    ```"""

    model_config = pydantic.ConfigDict(frozen=True, arbitrary_types_allowed=True)

    lat: int = pydantic.Field(..., ge=-90, le=90)
    lon: int = pydantic.Field(..., ge=-180, le=180)
    start_date: pendulum.Date = pydantic.Field(...)
    end_date: pendulum.Date = pydantic.Field(...)

    def slug(self, verbose: bool = False) -> str:
        """Return a slug for the location

        verbose = false: `48N011E``
        verbose = true: `48.00N_11.00E`"""

        str_ = f"{abs(self.lat):.2f}" if verbose else f"{abs(self.lat):02}"
        str_ += "S" if self.lat < 0 else "N"
        str_ += "_" if verbose else ""
        str_ += f"{abs(self.lon):.2f}" if verbose else f"{abs(self.lon):03}"
        return str_ + ("W" if self.lon < 0 else "E")
