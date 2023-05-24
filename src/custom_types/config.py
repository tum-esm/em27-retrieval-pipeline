from datetime import datetime
from typing import Literal, Optional
from .validator import apply_field_validator
import pydantic


class LocationDataConfig(pydantic.BaseModel):
    """Pydantic model:

    ```python
    github_repository: str
    access_token: Optional[str]
    ```
    """

    github_repository: str = pydantic.Field(..., regex=r"^[a-z0-9-_]+/[a-z0-9-_]+$")
    access_token: Optional[str]


class DataSrcDirsConfig(pydantic.BaseModel):
    """Pydantic model:

    ```python
    datalogger: str
    vertical_profiles: str
    interferograms: str
    ```
    """

    datalogger: str
    vertical_profiles: str
    interferograms: str

    # validators
    _1 = apply_field_validator(
        ["datalogger", "vertical_profiles", "interferograms"],
        "is_directory_path",
    )


class DataDstDirsConfig(pydantic.BaseModel):
    results: str

    # validators
    _1 = apply_field_validator(
        ["results"],
        "is_directory_path",
    )


class VerticalProfilesFTPServerConfig(pydantic.BaseModel):
    """Pydantic model:

    ```python
    email: str
    max_day_delay: int = 7
    upload_sleep: int = 60
    upload_timeout: int = 180
    download_sleep: int = 60
    download_timeout: int = 600
    ```
    """

    email: str = pydantic.Field(..., min_length=3)
    max_day_delay: int = pydantic.Field(7, ge=0, le=10)
    upload_sleep: int = pydantic.Field(60, ge=0)
    upload_timeout: int = pydantic.Field(180, ge=0)
    download_sleep: int = pydantic.Field(60, ge=0)
    download_timeout: int = pydantic.Field(600, ge=0)


class VerticalProfilesRequestScopeConfig(pydantic.BaseModel):
    """Pydantic model:

    ```python
    from_date: str = "19000101"
    to_date: str = datetime.utcnow().strftime("%Y%m%d")
    data_types: list[Literal["GGG2014", "GGG2020"]] = ["GGG2014", "GGG2020"]
    ```
    """

    from_date: str = "19000101"
    to_date: str = datetime.utcnow().strftime("%Y%m%d")
    data_types: list[Literal["GGG2014", "GGG2020"]] = ["GGG2014", "GGG2020"]

    # validators
    _1 = apply_field_validator(
        ["from_date", "to_date"],
        "is_date_string",
    )


class AutomatedProffastStorageDataFilterConfig(pydantic.BaseModel):
    """Pydantic model:

    ```python
    sensor_ids_to_consider: list[str]
    start_date: str
    end_date: str
    min_days_delay: int
    ```
    """

    sensor_ids_to_consider: list[str] = pydantic.Field(..., min_items=1)
    from_date: str
    to_date: str
    min_days_delay: int = pydantic.Field(..., ge=0, le=60)

    # validators
    _1 = apply_field_validator(
        ["from_date", "to_date"],
        "is_date_string",
    )


class AutomatedProffastModifiedIfgFilePermissionsConfig(pydantic.BaseModel):
    """Pydantic model:

    ```python
    during_processing: Optional[str]
    after_processing: Optional[str]
    ```
    """

    during_processing: Optional[str] = pydantic.Field(
        None, regex=r"^((r|-)(w|-)(x|-)){3}$"
    )
    """A unix-like file permission string, e.g. `rwxr-xr-x`."""

    after_processing: Optional[str] = pydantic.Field(
        None, regex=r"^((r|-)(w|-)(x|-)){3}$"
    )
    """A unix-like file permission string, e.g. `rwxr-xr-x`."""


class AutomatedProffastDataSourcesConfig(pydantic.BaseModel):
    """Pydantic model:

    ```python
    storage: bool
    manual_queue: bool
    ```
    """

    storage: bool
    manual_queue: bool


class GeneralConfig(pydantic.BaseModel):
    """Pydantic model:

    ```python
    location_data: LocationDataConfig
    data_src_dirs: DataSrcDirsConfig
    data_dst_dirs: DataDstDirsConfig
    ```
    """

    location_data: LocationDataConfig
    data_src_dirs: DataSrcDirsConfig
    data_dst_dirs: DataDstDirsConfig


class VerticalProfilesConfig(pydantic.BaseModel):
    """Pydantic model:

    ```python
    ftp_server: VerticalProfilesFTPServerConfig
    request_scope: VerticalProfilesRequestScopeConfig
    ```
    """

    ftp_server: VerticalProfilesFTPServerConfig
    request_scope: VerticalProfilesRequestScopeConfig


class AutomatedProffastConfig(pydantic.BaseModel):
    """Pydantic model:

    ```python
    max_core_count: int
    ifg_file_regex: str
    data_sources: AutomatedProffastDataSourcesConfig
    modified_ifg_file_permissions: AutomatedProffastModifiedIfgFilePermissionsConfig
    storage_data_filter: AutomatedProffastStorageDataFilterConfig
    ```
    """

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
    """Pydantic model:

    ```python
    campaign_id: str
    data_types: list[Literal[
        "gnd_p", "gnd_t", "app_sza", "azimuth",
        "xh2o", "xair", "xco2", "xch4", "xco", "xch4_s5p"
    ]]
    sampling_rate: str
    max_interpolation_gap_seconds: str
    dst_dir: str
    ```
    """

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
    _1 = apply_field_validator(
        ["dst_dir"],
        "is_directory",
    )


class Config(pydantic.BaseModel):
    general: GeneralConfig
    vertical_profiles: VerticalProfilesConfig
    automated_proffast: AutomatedProffastConfig
    output_merging_targets: list[OutputMergingTargetConfig]
