from pydantic import BaseModel, validator
from tum_esm_utils.validators import validate_str, validate_int


class ManualQueueItem(BaseModel):
    sensor_id: str
    date: str
    priority: int

    # validators
    _val_sensor_id = validator("sensor_id", pre=True, allow_reuse=True)(
        validate_str(min_len=1),
    )
    _val_date = validator("date", pre=True, allow_reuse=True)(
        validate_str(is_date_string=True),
    )
    _val_priority = validator("priority", pre=True, allow_reuse=True)(
        validate_int(forbidden=[0]),
    )


class ManualQueue(BaseModel):
    items: list[ManualQueueItem]
