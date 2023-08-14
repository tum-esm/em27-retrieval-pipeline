import datetime
from src import utils


def test_get_ils_params() -> None:
    for month in [1, 5, 11]:
        print(month)
        utils.proffast.get_ils_params(61, datetime.date(2020, month, 1))
        utils.proffast.get_ils_params(86, datetime.date(2021, month, 1))
        utils.proffast.get_ils_params(115, datetime.date(2022, month, 1))
        utils.proffast.get_ils_params(116, datetime.date(2023, month, 1))
        utils.proffast.get_ils_params(117, datetime.date(2024, month, 1))
