import pydantic
from ..validators import apply_field_validators


class ManualQueueItem(pydantic.BaseModel):
    sensor_id: str
    date: str = pydantic.Field(..., description="Date in YYYYMMDD format")
    priority: int = pydantic.Field(
        ...,
        ge=1,
        description="Priority of the item. Cannot be zero. Items with higher priority are processed first. If data from both the storage queue and the manual queue are considered, the storage queue items have a priority of zero.",
    )

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
    items: list[ManualQueueItem] = []
