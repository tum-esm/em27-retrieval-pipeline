import pydantic.errors
import pydantic.validators
from typing import Any

# this workaround is necessary because pydantic currently does
# not support strict validation on a whole Model. It converts
# the input to the datatype, i.e. "23" will not raise an error
# on int or float data types because it can be converted.

# Read https://github.com/pydantic/pydantic/issues/578 on the reason for this decision
# Watch https://github.com/pydantic/pydantic/issues/1098 for a possible fix


def _strict_bool_validator(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    raise pydantic.errors.BoolError()


def _strict_float_validator(v: Any) -> float:
    if isinstance(v, float) or isinstance(v, int):
        return v
    raise pydantic.errors.FloatError()


for i, (type_, _) in enumerate(pydantic.validators._VALIDATORS):
    if type_ == int:
        pydantic.validators._VALIDATORS[i] = (
            int,
            [pydantic.validators.strict_int_validator],
        )
    if type_ == float:
        pydantic.validators._VALIDATORS[i] = (float, [_strict_float_validator])
    if type_ == str:
        pydantic.validators._VALIDATORS[i] = (
            str,
            [pydantic.validators.strict_str_validator],
        )
    if type_ == bool:
        pydantic.validators._VALIDATORS[i] = (bool, [_strict_bool_validator])


class ValidationError(Exception):
    """
    Will be raised in any custom checks on config dicts
    have failed: file-existence, date-format
    """
