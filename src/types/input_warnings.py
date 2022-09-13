import os
import pydantic
from typing import Any, TypedDict
from .validation_error import ValidationError

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))


class InputWarningsDict(TypedDict):
    message: str
    last_checked: str


class _ValidationModel(pydantic.BaseModel):
    o: dict[str, InputWarningsDict]

    class Config:
        extra = "forbid"


def validate_input_warnings(o: Any) -> None:
    """
    Check, whether a given list is a correct list of ManualQueueItemDicts
    Raises a pydantic.ValidationError if the object is invalid.

    This should always be used when loading the object from a
    JSON file!
    """
    try:
        _ValidationModel(o=o)
    except pydantic.ValidationError as e:
        pretty_error_messages = []
        for error in e.errors():
            fields = [str(f) for f in error["loc"][1:] if f not in ["__root__"]]
            pretty_error_messages.append(f"{'.'.join(fields)} -> {error['msg']}")
        raise ValidationError(
            f"input warnings object is invalid: {', '.join(pretty_error_messages)}"
        )
