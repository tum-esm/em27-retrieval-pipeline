import datetime
import tomllib
import em27_metadata
import tum_esm_utils


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


def get_pipeline_version() -> str:
    """Returns the current version (`x.y.z`) of the pipeline."""

    with open(
        tum_esm_utils.files.rel_to_abs_path("../../pyproject.toml"), "rb"
    ) as f:
        try:
            v = tomllib.load(f)["project"]["version"]
            assert isinstance(v, str)
            return v
        except (KeyError, AssertionError):
            raise ValueError(
                "Could not find project version in `pyproject.toml`"
            )
