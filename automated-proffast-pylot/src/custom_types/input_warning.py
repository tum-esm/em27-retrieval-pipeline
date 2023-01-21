from pydantic import BaseModel, validator
from .validators import validate_str


class InputWarning(BaseModel):
    message: str
    last_checked: str

    # validators
    _val_str = validator(
        *["message", "last_checked"],
        pre=True,
        allow_reuse=True,
    )(validate_str())
