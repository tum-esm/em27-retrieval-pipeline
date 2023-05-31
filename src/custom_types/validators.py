from datetime import datetime
from typing import Any, TypeVar
import pydantic
import os


T = TypeVar("T")


def apply_field_validators(
    parameters: list[str],
    is_directory_path: bool = False,
    is_file_path: bool = False,
    is_date_string: bool = False,
    is_datetime_string: bool = False,
    forbidden_values: list[T] = [],
    required_list_items: list[T] = [],
) -> Any:
    """Advanced field validator for pydantic models. Usage example:

    ```python
    class Model(pydantic.BaseModel):
        a: str
        b: str
        c: str

        # validators
        _1 = apply_field_validators(
            ["a", "c"],
            is_directory_path=True,
            forbidden_values=["foo", "bar"],
        )
    """

    def f(cls: Any, v: T) -> T:
        if v is None:
            return None

        if is_directory_path:
            assert isinstance(v, str)
            if not os.path.isdir(v):
                raise ValueError(f'"{v}" is not an existing directory path')
            if v.endswith("/"):
                raise ValueError(f'directory path "{v}" cannot include a trailing "/"')

        if is_file_path:
            assert isinstance(v, str)
            if not os.path.isfile(v):
                raise ValueError(f'"{v}" is not an existing file path')

        if is_date_string:
            assert isinstance(v, str)
            try:
                datetime.strptime(v, "%Y%m%d")
            except ValueError:
                raise ValueError(f'"{v}" is not a date string ("YYYYMMDD")')

        if is_datetime_string:
            assert isinstance(v, str)
            try:
                datetime.strptime(v, "%Y%m%d %H:%M:%S")
            except ValueError:
                raise ValueError(
                    f'"{v}" is not a datetime string ("YYYYMMDD HH:mm:ss")'
                )

        if len(forbidden_values) > 0:
            if isinstance(v, list):
                for item in v:
                    if item in forbidden_values:
                        raise ValueError(
                            f'"{item}" is a forbidden value for this field'
                        )
            elif v in forbidden_values:
                raise ValueError(f'"{v}" is a forbidden value for this field')

        if len(required_list_items) > 0:
            if isinstance(v, list):
                for item in required_list_items:
                    if item not in v:
                        raise ValueError(f'"{item}" is a required value for this field')
            elif v not in required_list_items:
                raise ValueError(f'"{v}" is a required value for this field')

        return v

    return pydantic.validator(*parameters, pre=True, allow_reuse=True)(f)
