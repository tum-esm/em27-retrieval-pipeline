import datetime
import pydantic
from src import utils


class DownloadQuery(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)

    lat: int = pydantic.Field(..., ge=-90, le=90, frozen=True)
    lon: int = pydantic.Field(..., ge=-180, le=180, frozen=True)
    from_date: datetime.date = pydantic.Field(...)
    to_date: datetime.date = pydantic.Field(...)

    def to_coordinates_slug(self, verbose: bool = False) -> str:
        """Return a slug for the location

        verbose = false: `48N011E``
        verbose = true: `48.00N_11.00E`"""

        return utils.functions.get_coordinates_slug(self.lat, self.lon, verbose=verbose)

    def to_date_string(self, sep: str = "") -> str:
        return self.to_date.strftime(f"%Y{sep}%m{sep}%d")

    def from_date_string(self, sep: str = "") -> str:
        return self.from_date.strftime(f"%Y{sep}%m{sep}%d")
