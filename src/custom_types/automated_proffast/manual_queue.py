import pydantic
from ..validator import apply_field_validator


class ManualQueueItem(pydantic.BaseModel):
    sensor_id: str = pydantic.Field(..., min_length=1)
    date: str
    priority: int

    # validators
    _1 = apply_field_validator(
        ["date"],
        "is_date_string",
    )
    _2 = apply_field_validator(
        ["priority"],
        forbidden=[0],
    )


class ManualQueue(pydantic.BaseModel):
    items: list[ManualQueueItem]
