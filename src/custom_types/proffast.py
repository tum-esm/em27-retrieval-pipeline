import os
from typing import Any
import pydantic
import datetime
import tum_esm_em27_metadata.types
import tum_esm_utils

_PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=3)
_CONTAINERS_DIR = os.path.join(_PROJECT_DIR, "data", "containers")


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


class ProffastSession(pydantic.BaseModel):
    """This combines a `SensorDataContext` with a `Proffast10Container`/
    `Proffast22Container`/`Proffast23Container`."""

    ctx: tum_esm_em27_metadata.types.SensorDataContext
    ctn: Proffast10Container | Proffast22Container | Proffast23Container
