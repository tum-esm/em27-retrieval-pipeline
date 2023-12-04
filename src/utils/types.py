import datetime
import os
from typing import Any, Literal
import pydantic
import em27_metadata
import tum_esm_utils

_PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(
    __file__, current_depth=3
)
_CONTAINERS_DIR = os.path.join(_PROJECT_DIR, "data", "containers")


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

        lat = round(self.lat)
        lon = round(self.lon)

        str_ = f"{abs(lat):.2f}" if verbose else f"{abs(lat):02}"
        str_ += "S" if lat < 0 else "N"
        str_ += "_" if verbose else ""
        str_ += f"{abs(lon):.2f}" if verbose else f"{abs(lon):03}"
        return str_ + ("W" if lon < 0 else "E")

    def to_date_string(self, sep: str = "") -> str:
        return self.to_date.strftime(f"%Y{sep}%m{sep}%d")

    def from_date_string(self, sep: str = "") -> str:
        return self.from_date.strftime(f"%Y{sep}%m{sep}%d")


class InputWarning(pydantic.BaseModel):
    sensor_id: str
    from_datetime: datetime.datetime
    message: str
    last_checked: datetime.datetime

    @pydantic.field_serializer("from_datetime", "last_checked")
    def t_serializer(self, dt: datetime.datetime, _info: Any) -> str:
        return dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")


class InputWarningsList(pydantic.BaseModel):
    items: list[InputWarning]


class Proffast10Container(pydantic.BaseModel):
    container_id: str

    @property
    def container_path(self) -> str:
        return os.path.join(
            _CONTAINERS_DIR,
            f"pylot-container-{self.container_id}",
        )

    @property
    def data_input_path(self) -> str:
        return os.path.join(
            _CONTAINERS_DIR,
            f"pylot-container-{self.container_id}-inputs",
        )

    @property
    def data_output_path(self) -> str:
        return os.path.join(
            _CONTAINERS_DIR,
            f"pylot-container-{self.container_id}-outputs",
        )


class Proffast22Container(pydantic.BaseModel):
    container_id: str

    @property
    def container_path(self) -> str:
        return os.path.join(
            _CONTAINERS_DIR,
            f"pylot-container-{self.container_id}",
        )

    @property
    def data_input_path(self) -> str:
        return os.path.join(
            _CONTAINERS_DIR,
            f"pylot-container-{self.container_id}-inputs",
        )

    @property
    def data_output_path(self) -> str:
        return os.path.join(
            _CONTAINERS_DIR,
            f"pylot-container-{self.container_id}-outputs",
        )

    @property
    def pylot_config_path(self) -> str:
        return os.path.join(
            _CONTAINERS_DIR,
            f"pylot-container-{self.container_id}-inputs",
            "pylot_config.yml",
        )

    @property
    def pylot_log_format_path(self) -> str:
        return os.path.join(
            _CONTAINERS_DIR,
            f"pylot-container-{self.container_id}-inputs",
            "pylot_log_format.yml",
        )


class Proffast23Container(Proffast22Container):
    """No difference to `Proffast22Container`."""


ProffastContainer = Proffast10Container | Proffast22Container | Proffast23Container
RetrievalAlgorithm = Literal["proffast-1.0", "proffast-2.2", "proffast-2.3"]


class RetrievalSession(pydantic.BaseModel):
    """This combines a `SensorDataContext` with a `Proffast10Container`/
    `Proffast22Container`/`Proffast23Container`."""

    ctx: em27_metadata.types.SensorDataContext
    ctn: ProffastContainer
