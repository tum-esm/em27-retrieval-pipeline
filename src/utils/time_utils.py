
from datetime import datetime


class TimeUtils:

    def date_string_is_valid(date_string: str):
        try:
            datetime.strptime(date_string, "%Y%m%d")
            return True
        except ValueError:
            return False


    def delta_days_until_now(date_string: str):
        return (datetime.utcnow() - datetime.strptime(date_string, "%Y%m%d")).days
