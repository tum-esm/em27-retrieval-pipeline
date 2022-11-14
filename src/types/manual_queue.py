from datetime import datetime
import pydantic
from typing import Any, TypedDict
from .validation_error import ValidationError
from .config import ConfigDict


class ManualQueueItemDict(TypedDict):
    sensor: str
    date: str
    priority: int


class _ValidationModel(pydantic.BaseModel):
    o: list[ManualQueueItemDict]

    class Config:
        extra = "forbid"


def validate_manual_queue(o: Any, config: ConfigDict) -> None:
    """
    Check, whether a given list is a correct list of ManualQueueItemDicts
    Raises a pydantic.ValidationError if the object is invalid.

    This should always be used when loading the object from a
    JSON file!
    """
    try:
        _ValidationModel(o=o)
        assert isinstance(o, list)  # necessary due to pydantics autoconversion
    except pydantic.ValidationError as e:
        pretty_error_messages = []
        for error in e.errors():
            fields = [str(f) for f in error["loc"][1:] if f not in ["__root__"]]
            pretty_error_messages.append(f"{'.'.join(fields)} -> {error['msg']}")
        raise ValidationError(
            f"manual queue file is invalid: {', '.join(pretty_error_messages)}"
        )
    except AssertionError:
        raise ValidationError(
            f"manual queue file is invalid: has to be a list not a dict"
        )

    new_manual_queue: list[ManualQueueItemDict] = o

    try:
        for item in new_manual_queue:
            assert item["priority"] != 0, "priorities cannot be zero"
            try:
                datetime.strptime(item["date"], "%Y%m%d")
            except:
                raise AssertionError(f"config.start_date is not a valid date")
            assert (
                item["sensor"] in config["sensors_to_consider"]
            ), f'sensor {item["sensor"]} not in config.sensors_to_consider'

    except AssertionError as e:
        raise ValidationError(f"manual queue file is invalid: {e}")
