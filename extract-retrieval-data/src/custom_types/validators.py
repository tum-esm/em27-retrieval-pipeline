import datetime
import os
from typing import Any


def validate_strict_str(cls: Any, v: Any) -> str:
    if not isinstance(v, str):
        raise ValueError(f'"{v}" is not a string')
    return v


def validate_dir_path(cls: Any, v: str) -> str:
    if not os.path.isdir(v):
        raise ValueError(f'"{v}" is not a directory')
    return v


def validate_date_string(cls: Any, v: str) -> str:
    try:
        datetime.datetime.strptime(v, "%Y%m%d")
    except:
        raise ValueError(f'"{v}" is not a valid date')
    return v
