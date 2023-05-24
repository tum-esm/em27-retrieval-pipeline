import pydantic
from ..validators import apply_field_validators


class ManualQueueItem(pydantic.BaseModel):
    sensor_id: str = pydantic.Field(..., min_length=1)
    date: str
    priority: int

    # validators
    _1 = apply_field_validators(
        ["date"],
        is_date_string=True,
    )
    _2 = apply_field_validators(
        ["priority"],
        forbidden_values=[0],
    )


class ManualQueue(pydantic.BaseModel):
    items: list[ManualQueueItem]
