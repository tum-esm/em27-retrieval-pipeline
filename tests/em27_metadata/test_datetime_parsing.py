import datetime

import pydantic
import pytest
import src


@pytest.mark.em27_metadata_library
def test_datetime_parsing() -> None:
    assert src.em27_metadata.types.TimeSeriesElement.matches_datetime_regex(
        "2016-10-01T00:00:00+0000"
    )
    assert src.em27_metadata.types.TimeSeriesElement.matches_datetime_regex(
        "2016-10-01T23:00:00+0000"
    )
    assert src.em27_metadata.types.TimeSeriesElement.matches_datetime_regex(
        "2016-10-01T00:00:00+0100"
    )
    assert src.em27_metadata.types.TimeSeriesElement.matches_datetime_regex(
        "2016-10-01T00:00:00Z"
    )
    assert not src.em27_metadata.types.TimeSeriesElement.matches_datetime_regex(
        "2016-10-01T00:00:00+000"
    )


@pytest.mark.em27_metadata_library
def test_time_series_element() -> None:
    tse1 = src.em27_metadata.types.TimeSeriesElement(
        from_datetime="2016-10-01T00:00:00+0000",  # pyright: ignore[reportArgumentType]
        to_datetime="2016-10-01T22:59:59+0200",  # pyright: ignore[reportArgumentType]
    )
    assert tse1.from_datetime == "2016-10-01T00:00:00+0000"
    actual_dt_seconds = (
        tse1.to_datetime_parsed - tse1.from_datetime_parsed
    ).total_seconds()
    expected_dt_seconds = 3600 * 21 - 1
    assert actual_dt_seconds == expected_dt_seconds, (
        f"dt_seconds: {actual_dt_seconds} (actual) != {expected_dt_seconds} (expected)"
    )

    tse2 = src.em27_metadata.types.TimeSeriesElement(
        from_datetime="2016-10-01T00:00:00+0000",  # pyright: ignore[reportArgumentType]
        to_datetime="2016-10-03T13:24:59-0530",  # pyright: ignore[reportArgumentType]
    )
    actual_dt_seconds = (
        tse2.to_datetime_parsed - tse2.from_datetime_parsed
    ).total_seconds()
    expected_dt_seconds = 61 * 3600 + (24 * 60) + 59 + (5 * 3600) + (30 * 60)
    assert actual_dt_seconds == expected_dt_seconds, (
        f"dt_seconds: {actual_dt_seconds} (actual) != {expected_dt_seconds} (expected)"
    )


@pytest.mark.em27_metadata_library
def test_time_series_element_rejects_non_string_and_invalid_datetimes() -> None:
    with pytest.raises(pydantic.ValidationError):
        src.em27_metadata.types.TimeSeriesElement(
            from_datetime=datetime.datetime(2016, 10, 1),  # pyright: ignore[reportArgumentType]
            to_datetime="2016-10-01T23:59:59Z",
        )

    with pytest.raises(pydantic.ValidationError):
        src.em27_metadata.types.TimeSeriesElement(
            from_datetime="2016-02-30T00:00:00Z",
            to_datetime="2016-03-01T23:59:59Z",
        )
