import random
import datetime
from src.profiles.generate_queries_new import TimePeriod


def test_construct_time_periods() -> None:
    for _ in range(100):
        from_date = datetime.date(
            random.randint(2000, 2023),
            random.randint(1, 12),
            random.randint(1, 28),
        )
        to_date = from_date + datetime.timedelta(days=random.randint(1, 365))
        xs = TimePeriod.construct(from_date=from_date, to_date=to_date)
        assert len(xs) >= 1
        assert xs[0].from_date <= from_date
        assert xs[-1].to_date >= to_date
        assert all([x.from_date.weekday() == 0 for x in xs])
        assert all([x.to_date.weekday() == 6 for x in xs])
        assert all([
            x1.to_date == x2.from_date - datetime.timedelta(days=1)
            for x1, x2 in zip(xs[:-1], xs[1 :])
        ])


def test_minify_time_periods() -> None:
    ts = [
        TimePeriod(
            from_date=datetime.date(2021, 1, 1),
            to_date=datetime.date(2021, 1, 7),
        ),
        TimePeriod(
            from_date=datetime.date(2021, 1, 8),
            to_date=datetime.date(2021, 1, 14),
        ),
        TimePeriod(
            from_date=datetime.date(2021, 1, 15),
            to_date=datetime.date(2021, 1, 21),
        ),
        TimePeriod(
            from_date=datetime.date(2021, 1, 22),
            to_date=datetime.date(2021, 1, 28),
        ),
    ]
    present_dates = [
        # tp1 (all present)
        datetime.date(2021, 1, 1),
        datetime.date(2021, 1, 2),
        datetime.date(2021, 1, 3),
        datetime.date(2021, 1, 4),
        datetime.date(2021, 1, 5),
        datetime.date(2021, 1, 6),
        datetime.date(2021, 1, 7),

        # tp2 (part missing)
        datetime.date(2021, 1, 8),
        datetime.date(2021, 1, 9),
        datetime.date(2021, 1, 10),
        # datetime.date(2021, 1, 11),
        datetime.date(2021, 1, 12),
        datetime.date(2021, 1, 13),
        datetime.date(2021, 1, 14),

        # tp3 (part missing)
        datetime.date(2021, 1, 15),
        # datetime.date(2021, 1, 16),
        # datetime.date(2021, 1, 17),
        # datetime.date(2021, 1, 18),
        # datetime.date(2021, 1, 19),
        # datetime.date(2021, 1, 20),
        datetime.date(2021, 1, 21),

        # tp4 (all missing)
        # datetime.date(2021, 1, 22),
        # datetime.date(2021, 1, 23),
        # datetime.date(2021, 1, 24),
        # datetime.date(2021, 1, 25),
        # datetime.date(2021, 1, 26),
        # datetime.date(2021, 1, 27),
        # datetime.date(2021, 1, 28),
    ]
    assert TimePeriod.minify(
        present_dates=present_dates, all_time_periods=ts
    ) == [
        TimePeriod(
            from_date=datetime.date(2021, 1, 11),
            to_date=datetime.date(2021, 1, 11),
        ),
        TimePeriod(
            from_date=datetime.date(2021, 1, 16),
            to_date=datetime.date(2021, 1, 20),
        ),
        TimePeriod(
            from_date=datetime.date(2021, 1, 22),
            to_date=datetime.date(2021, 1, 28),
        ),
    ]
