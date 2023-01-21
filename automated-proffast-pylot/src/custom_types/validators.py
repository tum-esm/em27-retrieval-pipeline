from datetime import datetime
import os
import re
from typing import Any, Callable, Optional, TypeVar


def _is_date_string(date_string: str) -> bool:
    try:
        datetime.strptime(date_string, "%Y%m%d")
        return True
    except AssertionError:
        return False


def validate_bool() -> Callable[[Any, bool], bool]:
    def f(cls: Any, v: Any) -> bool:
        if not isinstance(v, bool):
            raise ValueError(f'"{v}" is not a boolean')
        return v

    return f


def validate_float(
    nullable: bool = False,
    minimum: Optional[float] = None,
    maximum: Optional[float] = None,
) -> Callable[[Any, float], float]:
    def f(cls: Any, v: float) -> float:
        if v is None:
            if nullable:
                return v
            else:
                raise ValueError(f"value cannot be None")
        if not isinstance(v, (int, float)):
            raise ValueError(f'"{v}" is not a float')
        if minimum is not None and v < minimum:
            raise ValueError(f'"{v}" is smaller than {minimum}')
        if maximum is not None and v > maximum:
            raise ValueError(f'"{v}" is larger than {maximum}')
        return v

    return f


def validate_int(
    nullable: bool = False,
    minimum: Optional[int] = None,
    maximum: Optional[int] = None,
    allowed: Optional[list[int]] = None,
    forbidden: Optional[list[int]] = None,
) -> Callable[[Any, Optional[int]], Optional[int]]:
    def f(cls: Any, v: Optional[int]) -> Optional[int]:
        if v is None:
            if nullable:
                return v
            else:
                raise ValueError(f"value cannot be None")
        if not isinstance(v, int):
            raise ValueError(f'"{v}" is not an integer')
        if minimum is not None and v < minimum:
            raise ValueError(f'"{v}" is smaller than {minimum}')
        if maximum is not None and v > maximum:
            raise ValueError(f'"{v}" is larger than {maximum}')
        if allowed is not None and v not in allowed:
            raise ValueError(f'"{v}" is not allowed (not one of {allowed})')
        if forbidden is not None and v in forbidden:
            raise ValueError(f'"{v}" is forbidden)')
        return v

    return f


def validate_str(
    nullable: bool = False,
    min_len: Optional[float] = None,
    max_len: Optional[float] = None,
    allowed: Optional[list[str]] = None,
    regex: Optional[str] = None,
    is_numeric: bool = False,
    is_directory: bool = False,
    is_file: bool = False,
    is_date_string: bool = False,
) -> Callable[[Any, str], str]:
    def f(cls: Any, v: str) -> str:
        if v is None:
            if nullable:
                return v
            else:
                raise ValueError(f"value cannot be None")
        if not isinstance(v, str):
            raise ValueError(f'"{v}" is not a string')
        if min_len is not None and len(v) < min_len:
            raise ValueError(f'"{v}" has less than {min_len} characters')
        if max_len is not None and len(v) > max_len:
            raise ValueError(f'"{v}" has more than {max_len} characters')
        if allowed is not None and v not in allowed:
            raise ValueError(f'"{v}" is not a allowed (not one of {allowed})')
        if regex is not None and re.compile(regex).match(v) is None:
            raise ValueError(f'"{v}" does not match the regex "{regex}"')
        if is_numeric and not v.isnumeric():
            raise ValueError(f'"{v}" is not numeric')
        if is_directory and not os.path.isdir(v):
            raise ValueError(f'"{v}" is not a directory')
        if is_file and not os.path.isfile(v):
            raise ValueError(f'"{v}" is not a file')
        if is_date_string and not _is_date_string(v):
            raise ValueError(f'"{v}" is not a day string ("YYYYMMDD")')
        return v

    return f


T = TypeVar("T")


def validate_list(
    min_len: Optional[float] = None,
    max_len: Optional[float] = None,
) -> Callable[[Any, list[T]], list[T]]:
    def f(cls: Any, v: list[T]) -> list[T]:
        if not isinstance(v, list):
            raise ValueError(f'"{v}" is not a list')
        if min_len is not None and len(v) < min_len:
            raise ValueError(f'"{v}" has less than {min_len} elements')
        if max_len is not None and len(v) > max_len:
            raise ValueError(f'"{v}" has more than {max_len} elements')
        return v

    return f
