from __future__ import annotations
import datetime
import pydantic


class DownloadQuery(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)

    lat: int = pydantic.Field(..., ge=-90, le=90, frozen=True)
    lon: int = pydantic.Field(..., ge=-180, le=180, frozen=True)
    from_date: datetime.date = pydantic.Field(..., frozen=True)
    to_date: datetime.date = pydantic.Field(...)

    def slug(self, verbose: bool = False) -> str:
        """Return a slug for the location

        verbose = false: `48N011E``
        verbose = true: `48.00N_11.00E`"""

        str_ = f"{abs(self.lat):.2f}" if verbose else f"{abs(self.lat):02}"
        str_ += "S" if self.lat < 0 else "N"
        str_ += "_" if verbose else ""
        str_ += f"{abs(self.lon):.2f}" if verbose else f"{abs(self.lon):03}"
        return str_ + ("W" if self.lon < 0 else "E")

    def to_date_string(self, sep: str = "") -> str:
        return self.to_date.strftime(f"%Y{sep}%m{sep}%d")

    def from_date_string(self, sep: str = "") -> str:
        return self.from_date.strftime(f"%Y{sep}%m{sep}%d")
