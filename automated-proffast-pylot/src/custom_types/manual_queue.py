from pydantic import BaseModel, validator
from .validators import validate_str, validate_int


class ManualQueueItem(BaseModel):
    sensor: str
    date: str
    priority: int

    # validators
    _val_sensor = validator("sensor", pre=True, allow_reuse=True)(
        validate_str(min_len=1),
    )
    _val_date = validator("date", pre=True, allow_reuse=True)(
        validate_str(is_date_string=True),
    )
    _val_priority = validator("priority", pre=True, allow_reuse=True)(
        validate_int(forbidden=[0]),
    )
