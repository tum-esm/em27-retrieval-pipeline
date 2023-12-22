import random
import datetime
from src.profiles.generate_queries_new import TimePeriod


def _date_range(
    from_date: datetime.date,
    to_date: datetime.date,
) -> list[datetime.date]:
    delta = to_date - from_date
    assert delta.days >= 0, "from_date must be before to_date"
    return [
        from_date + datetime.timedelta(days=i) for i in range(delta.days + 1)
    ]


def test_time_period_construction() -> None:
    for _ in range(100):
        from_date = datetime.date(
            random.randint(2000, 2023),
            random.randint(1, 12),
            random.randint(1, 28),
        )
        to_date = from_date + datetime.timedelta(days=random.randint(100, 365))
        requested_dates = random.sample(
            _date_range(from_date, to_date), random.randint(10, 100)
        )

        time_periods = TimePeriod.construct(
            requested_dates=set(requested_dates)
        )
        for tp1, tp2 in zip(time_periods[:-1], time_periods[1 :]):
            assert tp1.to_date < tp2.from_date

        actually_requested_dates: set[datetime.date] = set()
        for tp in time_periods:
            assert tp.from_date <= tp.to_date
            assert (tp.to_date - tp.from_date).days <= 6
            assert min(tp.requested_dates) == tp.from_date
            assert max(tp.requested_dates) == tp.to_date
            actually_requested_dates.update(tp.requested_dates)
        assert actually_requested_dates == set(requested_dates)
