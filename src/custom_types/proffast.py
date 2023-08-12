from typing import Any
import pydantic
import datetime
import tum_esm_em27_metadata.types


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


class PylotContainer(pydantic.BaseModel):
    # TODO: derived paths as properties based on container_id

    container_id: str
    container_path: str
    data_input_path: str
    data_output_path: str
    pylot_config_path: str
    pylot_log_format_path: str


class PylotSession(pydantic.BaseModel):
    """This combines a `SensorDataContext` with a `PylotContainer`."""

    ctx: tum_esm_em27_metadata.types.SensorDataContext
    ctn: PylotContainer
