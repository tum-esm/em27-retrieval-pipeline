from __future__ import annotations
from typing import Optional
import pydantic
import datetime


class TimePeriod(pydantic.BaseModel):
    from_date: datetime.date
    to_date: datetime.date

    def possible_to_dates(self) -> list[datetime.date]:
        """Returns a list of possible to_dates for this time period. This is
        because when requesting dates 1 to 7, the server might only return 1
        to 5 because 6 and 7 cannot be generated yet."""

        return [self.to_date - datetime.timedelta(days=i) for i in range(7)]

    def reduce_self(
        self,
        present_dates: list[datetime.date],
    ) -> Optional[TimePeriod]:
        """Given a list of dates already downloaded, remove the dates at
        the beginning and the end of this query that are in that list.
        
        Queries will be cut at the end if the requested scope is extented
        to the past after downloading some data. Queries will be cut at the
        beginning if this time period has already been downloaded, but only
        the beginning of it could be downloaded."""

        if self.from_date in present_dates:
            if self.from_date == self.to_date:
                return None
            else:
                return TimePeriod(
                    from_date=self.from_date + datetime.timedelta(days=1),
                    to_date=self.to_date,
                ).reduce_self(present_dates)
        elif self.to_date in present_dates:
            return TimePeriod(
                from_date=self.from_date,
                to_date=self.to_date - datetime.timedelta(days=1),
            ).reduce_self(present_dates)
        else:
            return self
    
    @staticmethod
    def construct(
        from_date: datetime.date,
        to_date: datetime.date,
    ) -> list[TimePeriod]:
        """Given a start and end date, construct a list of time periods
        that cover the whole range. The time periods will be weeks, starting
        on Monday and ending on Sunday."""

        time_periods: list[TimePeriod] = []
        current_date = from_date
        while current_date <= to_date:
            current_date -= datetime.timedelta(days=current_date.weekday())
            time_periods.append(
                TimePeriod(
                    from_date=current_date,
                    to_date=current_date + datetime.timedelta(days=6)
                )
            )
            current_date += datetime.timedelta(days=7)
        return time_periods


    @staticmethod
    def minify(
        present_dates: list[datetime.date],
        time_periods: list[TimePeriod],
    ) -> list[TimePeriod]:
        """Given a list of time periods and a list of dates already
        downloaded, remove the dates at the beginning and the end of each
        time period that are in that list. This is done so that this client
        is not requesting data that has already been downloaded."""

        minified_time_periods: list[Optional[TimePeriod]] = []
        for time_period in time_periods:
            minified_time_periods.append(time_period.reduce_self(
                list(
                    filter(
                        lambda x: x >= time_period.from_date and x <= time_period.
                        to_date, present_dates
                    )
                )
            ))
        return [tp for tp in minified_time_periods if tp is not None]

