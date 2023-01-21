from pydantic import BaseModel


class InputWarning(BaseModel):
    message: str
    last_checked: str
