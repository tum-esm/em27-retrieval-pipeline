import datetime

import pydantic
import pytest

import src


@pytest.mark.quick
def test_config_dates_remain_strings_and_have_parsed_properties() -> None:
    scope = src.types.GGGProfilesDownloaderSubConfigs.Scope(
        from_date="2024-02-01",
        to_date="2024-02-29",
        models=["GGG2020"],
    )

    assert scope.from_date == "2024-02-01"
    assert scope.to_date == "2024-02-29"
    assert scope.from_date_parsed == datetime.date(2024, 2, 1)
    assert scope.to_date_parsed == datetime.date(2024, 2, 29)

    with pytest.raises(pydantic.ValidationError):
        src.types.GGGProfilesDownloaderSubConfigs.Scope(
            from_date=datetime.date(2024, 2, 1),  # pyright: ignore[reportArgumentType]
            to_date="2024-02-29",
            models=["GGG2020"],
        )

    with pytest.raises(pydantic.ValidationError):
        src.types.GGGProfilesDownloaderSubConfigs.Scope(
            from_date="2024-02-30",
            to_date="2024-03-01",
            models=["GGG2020"],
        )


@pytest.mark.quick
def test_export_datetimes_accept_only_explicit_utc_strings() -> None:
    geoms_export = src.types.GEOMSExportConfig(
        sensor_ids=["ma"],
        retrieval_algorithms=["proffast-2.4"],
        atmospheric_profile_models=["GGG2020"],
        from_datetime="2024-01-01T00:00:00Z",
        to_datetime="2024-01-01T23:59:59Z",
    )
    assert geoms_export.from_datetime == "2024-01-01T00:00:00Z"
    assert geoms_export.from_datetime_parsed.tzinfo == datetime.timezone.utc

    bundle_export = src.types.BundleExportConfig.model_validate(
        {
            "dst_dir": "/tmp",
            "output_formats": ["parquet"],
            "from_datetime": "2024-01-01T00:00:00+0000",
            "to_datetime": "2024-01-01T23:59:59+0000",
            "retrieval_algorithms": ["proffast-2.4"],
            "atmospheric_profile_models": ["GGG2020"],
            "sensor_ids": ["ma"],
        }
    )
    assert bundle_export.to_datetime == "2024-01-01T23:59:59+0000"
    assert bundle_export.to_datetime_parsed.tzinfo == datetime.timezone.utc

    with pytest.raises(pydantic.ValidationError):
        src.types.GEOMSExportConfig.model_validate(
            {
                **geoms_export.model_dump(),
                "from_datetime": "2024-01-01T00:00:00+0100",
            }
        )

    with pytest.raises(pydantic.ValidationError):
        src.types.BundleExportConfig.model_validate(
            {
                **bundle_export.model_dump(),
                "from_datetime": "2024-01-01T00:00:00+0100",
            }
        )


@pytest.mark.quick
def test_geoms_calibration_datetimes_accept_only_explicit_utc_strings() -> None:
    calibration = src.types.GEOMSMetadataFields.CalibrationFactors(
        sensor_id="ma",
        valid_from_datetime="2024-01-01T00:00:00Z",
        valid_to_datetime="2024-12-31T23:59:59+0000",
        xco2=1,
        xch4=1,
        xco=1,
        xh2o=1,
    )
    assert calibration.valid_from_datetime == "2024-01-01T00:00:00Z"
    assert calibration.valid_to_datetime_parsed.tzinfo == datetime.timezone.utc

    with pytest.raises(pydantic.ValidationError):
        src.types.GEOMSMetadataFields.CalibrationFactors(
            sensor_id="ma",
            valid_from_datetime="2024-01-01T00:00:00-0100",
            valid_to_datetime="2024-12-31T23:59:59Z",
            xco2=1,
            xch4=1,
            xco=1,
            xh2o=1,
        )
