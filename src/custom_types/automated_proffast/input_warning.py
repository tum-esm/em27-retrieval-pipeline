import pydantic
from ..validators import apply_field_validators


class InputWarning(pydantic.BaseModel):
    sensor_id: str
    date: str
    message: str
    last_checked: str

    # validators
    _1 = apply_field_validators(
        ["date"],
        is_date_string=True,
    )


class InputWarningsList(pydantic.BaseModel):
    items: list[InputWarning]
