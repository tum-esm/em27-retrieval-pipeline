from datetime import date
from datetime import datetime

def str_to_date(value: str | date) -> date:
    match value:
        case date():
            return value
        case str():
            try:
                return datetime.strptime(value, "%Y%m%d").date()
            except ValueError as e:
                raise ValueError(f"Date format must be %Y%m%d") from e
        case _:
            raise TypeError(f"Date must be <class 'str'>")