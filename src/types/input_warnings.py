import datetime

import pydantic


class InputWarning(pydantic.BaseModel):
    sensor_id: str
    from_datetime: datetime.datetime
    message: str
    last_checked: datetime.datetime


class InputWarningsList(pydantic.RootModel[list[InputWarning]]):
    root: list[InputWarning]
