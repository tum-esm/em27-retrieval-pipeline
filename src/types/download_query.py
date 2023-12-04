import datetime
import pydantic


class DownloadQuery(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)

    lat: int = pydantic.Field(..., ge=-90, le=90, frozen=True)
    lon: int = pydantic.Field(..., ge=-180, le=180, frozen=True)
    from_date: datetime.date = pydantic.Field(...)
    to_date: datetime.date = pydantic.Field(...)

    @property
    def to_date_str(self, sep: str = "") -> str:
        return self.to_date.strftime(f"%Y{sep}%m{sep}%d")

    @property
    def from_date_str(self, sep: str = "") -> str:
        return self.from_date.strftime(f"%Y{sep}%m{sep}%d")
