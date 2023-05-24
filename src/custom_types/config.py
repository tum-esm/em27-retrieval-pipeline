from datetime import datetime
from typing import Literal, Optional
from .validators import apply_field_validators
import pydantic


class LocationDataConfig(pydantic.BaseModel):
    github_repository: str = pydantic.Field(..., regex=r"^[a-z0-9-_]+/[a-z0-9-_]+$")
    access_token: Optional[str]


class DataSrcDirsConfig(pydantic.BaseModel):
    datalogger: str
    vertical_profiles: str
    interferograms: str

    # validators
    _1 = apply_field_validators(
        ["datalogger", "vertical_profiles", "interferograms"],
        is_directory_path=True,
    )


class DataDstDirsConfig(pydantic.BaseModel):
    results: str

    # validators
    _1 = apply_field_validators(
        ["results"],
        is_directory_path=True,
    )


class VerticalProfilesFTPServerConfig(pydantic.BaseModel):
    email: str = pydantic.Field(..., min_length=3)
    max_day_delay: int = pydantic.Field(7, ge=0, le=10)
    upload_sleep: int = pydantic.Field(60, ge=0)
    upload_timeout: int = pydantic.Field(180, ge=0)
    download_sleep: int = pydantic.Field(60, ge=0)
    download_timeout: int = pydantic.Field(600, ge=0)


class VerticalProfilesRequestScopeConfig(pydantic.BaseModel):
    from_date: str = "19000101"
    to_date: str = datetime.utcnow().strftime("%Y%m%d")
    data_types: list[Literal["GGG2014", "GGG2020"]] = ["GGG2014", "GGG2020"]

    # validators
    _1 = apply_field_validators(
        ["from_date", "to_date"],
        is_date_string=True,
    )


class AutomatedProffastStorageDataFilterConfig(pydantic.BaseModel):
    sensor_ids_to_consider: list[str] = pydantic.Field(..., min_items=1)
    from_date: str
    to_date: str
    min_days_delay: int = pydantic.Field(..., ge=0, le=60)

    # validators
    _1 = apply_field_validators(
        ["from_date", "to_date"],
        is_date_string=True,
    )


class AutomatedProffastModifiedIfgFilePermissionsConfig(pydantic.BaseModel):
    during_processing: Optional[str] = pydantic.Field(
        None, regex=r"^((r|-)(w|-)(x|-)){3}$"
    )
    """A unix-like file permission string, e.g. `rwxr-xr-x`."""

    after_processing: Optional[str] = pydantic.Field(
        None, regex=r"^((r|-)(w|-)(x|-)){3}$"
    )
    """A unix-like file permission string, e.g. `rwxr-xr-x`."""


class AutomatedProffastDataSourcesConfig(pydantic.BaseModel):
    storage: bool
    manual_queue: bool


class GeneralConfig(pydantic.BaseModel):
    location_data: LocationDataConfig
    data_src_dirs: DataSrcDirsConfig
    data_dst_dirs: DataDstDirsConfig


class VerticalProfilesConfig(pydantic.BaseModel):
    ftp_server: VerticalProfilesFTPServerConfig
    request_scope: VerticalProfilesRequestScopeConfig


class AutomatedProffastConfig(pydantic.BaseModel):
    max_core_count: int = pydantic.Field(..., ge=1, le=64)

    ifg_file_regex: str = pydantic.Field(..., min_length=1)
    """A regex string to match the ifg file names.
    
    For example `^$(SENSOR_ID)$(DATE).*\\.\\d+$`. In this string, `$(SENSOR_ID)`
    and `$(DATE)` are placeholders for the sensor id and the date of the ifg
    file."""

    data_sources: AutomatedProffastDataSourcesConfig
    modified_ifg_file_permissions: AutomatedProffastModifiedIfgFilePermissionsConfig
    storage_data_filter: AutomatedProffastStorageDataFilterConfig


class OutputMergingTargetConfig(pydantic.BaseModel):
    campaign_id: str
    data_types: list[
        Literal[
            "gnd_p",
            "gnd_t",
            "app_sza",
            "azimuth",
            "xh2o",
            "xair",
            "xco2",
            "xch4",
            "xco",
            "xch4_s5p",
        ]
    ]
    sampling_rate: Literal[
        "10m", "5m", "2m", "1m", "30s", "15s", "10s", "5s", "2s", "1s"
    ]
    max_interpolation_gap_seconds: int = pydantic.Field(..., ge=6, le=43200)
    dst_dir: str

    # validators
    _1 = apply_field_validators(
        ["dst_dir"],
        is_directory_path=True,
    )


class Config(pydantic.BaseModel):
    general: GeneralConfig
    vertical_profiles: VerticalProfilesConfig
    automated_proffast: AutomatedProffastConfig
    output_merging_targets: list[OutputMergingTargetConfig]
