from pydantic import BaseModel, validator
from .validators import validate_str


class InputWarning(BaseModel):
    sensor_id: str
    date: str
    message: str
    last_checked: str

    # validators
    _val_str = validator(
        *["sensor_id", "message", "last_checked"],
        pre=True,
        allow_reuse=True,
    )(validate_str())

    _val_date = validator(
        "date",
        pre=True,
        allow_reuse=True,
    )(validate_str(is_date_string=True))


class InputWarningsList(BaseModel):
    items: list[InputWarning]
