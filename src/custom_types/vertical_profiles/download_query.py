from __future__ import annotations
import pendulum
import pydantic


class DownloadQuery(pydantic.BaseModel):
    """Pydantic model:

    ```python
    lat: int
    lon: int
    start_date: pendulum.Date
    end_date: pendulum.Date
    ```
    """

    model_config = pydantic.ConfigDict(frozen=True, arbitrary_types_allowed=True)

    lat: int = pydantic.Field(..., ge=-90, le=90)
    lon: int = pydantic.Field(..., ge=-180, le=180)
    start_date: pendulum.Date = pydantic.Field(...)
    end_date: pendulum.Date = pydantic.Field(...)

    def slug(self, verbose: bool = False) -> str:
        """Return a slug for the location

        verbose = false: `48N011E``
        verbose = true: `48.00N_11.00E`"""

        str_ = f"{abs(self.lat):.2f}" if verbose else f"{abs(self.lat):02}"
        str_ += "S" if self.lat < 0 else "N"
        str_ += "_" if verbose else ""
        str_ += f"{abs(self.lon):.2f}" if verbose else f"{abs(self.lon):03}"
        return str_ + ("W" if self.lon < 0 else "E")

    def remove_present_dates(
        self, present_dates: list[pendulum.Date]
    ) -> list[DownloadQuery]:
        """Remove dates from the query that are already present locally"""

        present_dates = list[
            sorted(
                filter(lambda d: self.start_date <= d <= self.end_date, present_dates)
            )
        ]
        while True:
            if len(present_dates) == 0:
                return [self]

            if present_dates[0] == self.start_date:
                self.start_date = self.start_date.add(days=1)
                present_dates.pop(0)
                continue
            if present_dates[-1] == self.end_date:
                self.end_date = self.end_date.subtract(days=1)
                present_dates.pop(-1)
                continue

            first_date = present_dates.pop(0)

            return [
                DownloadQuery(
                    lat=self.lat,
                    lon=self.lon,
                    start_date=self.start_date,
                    end_date=first_date.subtract(days=1),
                ),
                *DownloadQuery(
                    lat=self.lat,
                    lon=self.lon,
                    start_date=first_date.add(days=1),
                    end_date=self.end_date,
                ).remove_present_dates(present_dates),
            ]

    def split_large_queries(self, max_days_per_query: int = 28) -> list[DownloadQuery]:
        """If the queries are longer than the specified number of days,
        split them into multiple queries."""

        d = self.end_date - self.start_date
        assert isinstance(d, pendulum.Period)

        if d.days <= max_days_per_query:
            return [self]

        return [
            DownloadQuery(
                lat=self.lat,
                lon=self.lon,
                start_date=self.start_date,
                end_date=self.start_date.add(days=max_days_per_query - 1),
            ),
            *DownloadQuery(
                lat=self.lat,
                lon=self.lon,
                start_date=self.start_date.add(days=max_days_per_query),
                end_date=self.end_date,
            ).split_large_queries(max_days_per_query),
        ]
