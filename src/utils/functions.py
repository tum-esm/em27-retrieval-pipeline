import datetime
import em27_metadata


def date_range(
    from_date: datetime.date,
    to_date: datetime.date,
) -> list[datetime.date]:
    delta = to_date - from_date
    assert delta.days >= 0, "from_date must be before to_date"
    return [
        from_date + datetime.timedelta(days=i) for i in range(delta.days + 1)
    ]


def sdc_covers_the_full_day(
    sdc: em27_metadata.types.SensorDataContext,
) -> bool:
    return ((
        sdc.from_datetime.time().replace(microsecond=0)
        == datetime.time.min.replace(microsecond=0)
    ) and (
        sdc.to_datetime.time().replace(microsecond=0)
        == datetime.time.max.replace(microsecond=0)
    ))
