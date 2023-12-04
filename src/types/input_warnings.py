from typing import Any
import datetime
import pydantic


class InputWarning(pydantic.BaseModel):
    sensor_id: str
    from_datetime: datetime.datetime
    message: str
    last_checked: datetime.datetime

    @pydantic.field_serializer("from_datetime", "last_checked")
    def t_serializer(self, dt: datetime.datetime, _info: Any) -> str:
        return dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")


class InputWarningsList(pydantic.RootModel[list[InputWarning]]):
    root: list[InputWarning]
