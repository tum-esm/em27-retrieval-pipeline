from typing import Any


def validate_strict_str(cls: Any, v: Any) -> str:
    if not isinstance(v, str):
        raise ValueError('"{v}" is not a string')
    return v
