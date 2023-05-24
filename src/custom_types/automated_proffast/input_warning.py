import pydantic
from ..validator import apply_field_validator


class InputWarning(pydantic.BaseModel):
    sensor_id: str
    date: str
    message: str
    last_checked: str

    # validators
    _1 = apply_field_validator(
        ["date"],
        "is_date_string",
    )


class InputWarningsList(pydantic.BaseModel):
    items: list[InputWarning]
