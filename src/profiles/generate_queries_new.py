from __future__ import annotations
import pydantic
import datetime


class TimePeriod(pydantic.BaseModel):
    from_date: datetime.date
    to_date: datetime.date
    requested_dates: list[datetime.date]

    def possible_to_dates(self) -> list[datetime.date]:
        """Returns a list of possible to_dates for this time period. This is
        because when requesting dates 1 to 7, the server might only return 1
        to 5 because 6 and 7 cannot be generated yet."""

        return [self.to_date - datetime.timedelta(days=i) for i in range(7)]

    @staticmethod
    def construct(requested_dates: set[datetime.date]) -> list[TimePeriod]:
        """Given a start and end date, construct a list of time periods
        that cover the whole range. The time periods will be weeks, starting
        on Monday and ending on Sunday."""
        time_periods: list[TimePeriod] = []
        for d in sorted(requested_dates):
            if (len(time_periods) == 0) or (d > time_periods[-1].to_date):
                time_periods.append(
                    TimePeriod(
                        from_date=d - datetime.timedelta(days=d.weekday()),
                        to_date=d + datetime.timedelta(days=6 - d.weekday()),
                        requested_dates=[d]
                    )
                )
            else:
                time_periods[-1].requested_dates.append(d)

        for tp in time_periods:
            tp.from_date = min(tp.requested_dates)
            tp.to_date = max(tp.requested_dates)
        return time_periods
