import random
import datetime
import src
from src.profiles.generate_queries import (
    list_downloaded_data,
    list_requested_data,
    compute_missing_data,
    compute_time_periods,
)


def test_time_period_generation() -> None:
    for _ in range(100):
        from_date = datetime.date(
            random.randint(2000, 2023),
            random.randint(1, 12),
            random.randint(1, 28),
        )
        to_date = from_date + datetime.timedelta(days=random.randint(100, 365))
        required_dates = set(
            random.sample(
                src.utils.functions.date_range(from_date, to_date),
                random.randint(10, 100)
            )
        )
        time_periods = sorted(
            compute_time_periods(required_dates), key=lambda tp: tp.from_date
        )
        for tp1, tp2 in zip(time_periods[:-1], time_periods[1 :]):
            assert tp1.to_date < tp2.from_date
        requested_dates: set[datetime.date] = set()
        for tp in time_periods:
            assert 0 <= (tp.to_date - tp.from_date).days <= 6
            requested_dates.update(
                src.utils.functions.date_range(tp.from_date, tp.to_date)
            )
        assert requested_dates.issuperset(required_dates)
