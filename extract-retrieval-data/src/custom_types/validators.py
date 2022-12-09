from typing import Any, Callable

import re
import os
from datetime import datetime


def validate_bool() -> Callable[[Any, bool], bool]:
    def f(cls: Any, v: Any) -> bool:
        if not isinstance(v, bool):
            raise ValueError(f'"{v}" is not a boolean')
        return v

    return f


def validate_str(
    regex: str | None = None,
    is_date: bool = False,
    is_dir: bool = False,
) -> Callable[[Any, str], str]:
    def f(cls: Any, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError(f'"{v}" is not a string')
        if regex is not None and re.compile(regex).match(v) is None:
            raise ValueError(f'"{v}" does not match the regex "{regex}"')
        if is_dir and not os.path.isdir(v):
            raise ValueError(f'"{v}" is not a directory')
        if is_date:
            try:
                datetime.strptime(v, "%Y%m%d")
            except:
                raise ValueError(f'"{v}" is not a valid date')
        return v

    return f
