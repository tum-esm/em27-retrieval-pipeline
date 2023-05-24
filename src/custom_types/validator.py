from datetime import datetime
import os
from typing import Any, Literal, TypeVar
import pydantic


def apply_field_validator(
    parameters: list[str],
    validation_type: Literal[
        "is_directory_path",
        "is_file_path",
        "is_date_string",
        "is_datetime_string",
    ],
):
    T = TypeVar("T")

    def f(cls: Any, v: T) -> T:
        if v is None:
            return None
        if validation_type == "is_directory_path":
            assert isinstance(v, str)
            if not os.path.isdir(v):
                raise ValueError(f'"{v}" is not an existing directory path')
        elif validation_type == "is_file_path":
            assert isinstance(v, str)
            if not os.path.isfile(v):
                raise ValueError(f'"{v}" is not an existing file path')
        elif validation_type == "is_date_string":
            assert isinstance(v, str)
            try:
                datetime.strptime(v, "%Y%m%d")
            except ValueError:
                raise ValueError(f'"{v}" is not a date string ("YYYYMMDD")')
        elif validation_type == "is_datetime_string":
            assert isinstance(v, str)
            try:
                datetime.strptime(v, "%Y%m%d %H:%M:%S")
            except ValueError:
                raise ValueError(
                    f'"{v}" is not a datetime string ("YYYYMMDD HH:mm:ss")'
                )
        else:
            raise ValueError(f"Unknown validation type {validation_type}")
        return v

    return pydantic.validator(*parameters, pre=True, allow_reuse=True)(f)
