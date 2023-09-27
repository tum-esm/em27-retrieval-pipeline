from __future__ import annotations
import datetime
import os
from typing import Any, Literal, Optional
import tum_esm_utils
import pydantic


class LocationDataConfig(pydantic.BaseModel):
    """GitHub repository where the location data is stored"""

    github_repository: str = pydantic.Field(
        ...,
        pattern=r"^[a-z0-9-_]+/[a-z0-9-_]+$",
        description="GitHub repository name, e.g. `my-org/my-repo`",
    )

    access_token: Optional[str] = pydantic.Field(
        None,
        min_length=1,
        description=
        "GitHub access token with read access to the repository, only required if the repository is private",
    )


class DataSrcDirsConfig(pydantic.BaseModel):
    """Location where the input data sourced from"""

    datalogger: str = pydantic.Field(
        ..., description="directory path to datalogger files"
    )
    profiles: str = pydantic.Field(
        ..., description="directory path to vertical profile files"
    )
    interferograms: str = pydantic.Field(
        ..., description="directory path to ifg files"
    )


class DataDstDirsConfig(pydantic.BaseModel):
    results: str = pydantic.Field(..., description="directory path to results")


class VerticalProfilesFTPServerConfig(pydantic.BaseModel):
    """Settings for accessing the ccycle ftp server. Besides the
    `email` field, these can be left as default in most cases."""

    email: str = pydantic.Field(
        ...,
        min_length=3,
        description="email address to use to log in to the ccycle ftp server",
    )
    max_day_delay: int = pydantic.Field(
        7,
        ge=0,
        le=10,
        description=
        "maximum number of days of data availability delay of the ccycle ftp server. For example, on day 20 with `max delay = 7` the server should have data up to at least day 13. This is necessary because when requesting data from day 1-20 the output file might be names `day_1_13.tar` or `day_1_14.tar` -> with a delay of 7 days, the download process does not look for possible files named `day_1_12.tar`, `day_1_11.tar.`, etc.",
    )
    upload_sleep: int = pydantic.Field(60, ge=0, description="TODO")
    upload_timeout: int = pydantic.Field(180, ge=0, description="TODO")
    download_sleep: int = pydantic.Field(60, ge=0, description="TODO")
    download_timeout: int = pydantic.Field(
        600,
        ge=0,
        description="in seconds, how long to wait for a `.tar` " +
        "file to be generated before aborting the download",
    )


class VerticalProfilesRequestScopeConfig(pydantic.BaseModel):
    from_date: datetime.date = pydantic.Field(
        datetime.date(1900, 1, 1),
        description=
        "date in format `YYYY-MM-DD` from which to request vertical profile data",
    )
    to_date: datetime.date = pydantic.Field(
        datetime.date(2100, 1, 1),
        description=
        "date in format `YYYY-MM-DD` until which to request vertical profile data",
    )
    data_types: list[Literal["GGG2014", "GGG2020"]] = pydantic.Field(
        ["GGG2014", "GGG2020"],
        min_length=1,
        description="list of data types to request from the ccycle ftp server",
    )

    @pydantic.field_serializer("from_date", "to_date")
    def t_serializer(self, dt: datetime.date, _info: Any) -> str:
        return dt.strftime("%Y-%m-%d")


class AutomatedProffastGeneralConfig(pydantic.BaseModel):
    max_core_count: int = pydantic.Field(
        1,
        ge=1,
        le=64,
        description=
        "How many cores to use for parallel processing. There will be one process per sensor-day.",
    )

    ifg_file_regex: str = pydantic.Field(
        r"^$(SENSOR_ID)$(DATE).*\.\d+$",
        min_length=1,
        description=
        "A regex string to match the ifg file names. In this string, `$(SENSOR_ID)` and `$(DATE)` are placeholders for the sensor id and the date of the ifg file.",
    )

    retrieval_software: Literal[
        "proffast-1.0", "proffast-2.2", "proffast-2.3"] = pydantic.Field(
            ...,
            description="Which retrieval software to use.",
        )


class AutomatedProffastModifiedIfgFilePermissionsConfig(pydantic.BaseModel):
    during_processing: Optional[str] = pydantic.Field(
        None,
        pattern=r"^((r|-)(w|-)(x|-)){3}$",
        description=
        "A unix-like file permission string, e.g. `rwxr-xr-x`. This can be used to make the ifg files read-only during processing, to avoid accidental modification. Only used if not `null`.",
    )

    after_processing: Optional[str] = pydantic.Field(
        None,
        pattern=r"^((r|-)(w|-)(x|-)){3}$",
        description=
        "A unix-like file permission string, e.g. `rwxr-xr-x`. Same as `during_processing`, but restoring the permissions after processing. Only used if not `null`.",
    )


class AutomatedProffastDataFilterConfig(pydantic.BaseModel):
    """Settings for filtering the storage data. Only used if `config.data_sources.storage` is `true`."""

    sensor_ids_to_consider: list[str] = pydantic.Field(
        ...,
        min_length=1,
        description="Sensor ids to consider in the retrieval"
    )
    from_date: datetime.date = pydantic.Field(
        datetime.date(1900, 1, 1),
        description=
        "Date string in format `YYYY-MM-DD` from which to consider data in the storage directory",
    )
    to_date: datetime.date = pydantic.Field(
        datetime.date(2100, 1, 1),
        description=
        "Date string in format `YYYY-MM-DD` until which to consider data in the storage directory",
    )
    min_days_delay: int = pydantic.Field(
        5,
        ge=0,
        le=60,
        description=
        "Minimum numbers of days to wait until processing. E.g. the vertical profiles from ccyle are available with a delay of 5 days, so it doesn't make sence to try processing earlier and get a lot of error messages because of missing vertical profiles.",
    )

    @pydantic.field_serializer("from_date", "to_date")
    def t_serializer(self, dt: datetime.date, _info: Any) -> str:
        return dt.strftime("%Y-%m-%d")


class GeneralConfig(pydantic.BaseModel):
    location_data: LocationDataConfig
    data_src_dirs: DataSrcDirsConfig
    data_dst_dirs: DataDstDirsConfig


class VerticalProfilesConfig(pydantic.BaseModel):
    """Settings for vertical profiles retrieval. If `null`, the vertical profiles script will stop and log a warning"""

    ftp_server: VerticalProfilesFTPServerConfig
    request_scope: VerticalProfilesRequestScopeConfig


class AutomatedProffastConfig(pydantic.BaseModel):
    """Settings for automated proffast processing. If `null`, the automated proffast script will stop and log a warning"""

    general: AutomatedProffastGeneralConfig
    modified_ifg_file_permissions: AutomatedProffastModifiedIfgFilePermissionsConfig
    data_filter: AutomatedProffastDataFilterConfig


class OutputMergingTargetConfig(pydantic.BaseModel):
    campaign_id: str = pydantic.Field(
        ..., description="Campaign specified in location metadata."
    )
    sampling_rate: Literal["10m", "5m", "2m", "1m", "30s", "15s", "10s", "5s",
                           "2s", "1s"] = pydantic.Field(
                               ...,
                               description="Interval of resampled data.",
                           )
    dst_dir: str = pydantic.Field(
        ...,
        description="Directory to write the output to.",
    )
    data_types: list[Literal[
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
    ]] = pydantic.Field(
        [
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
        ],
        min_length=1,
        description=
        "Data columns to keep in the merged output files. The columns will be prefixed with the sensor id, i.e. `$(SENSOR_ID)_$(COLUMN_NAME)`.",
    )
    max_interpolation_gap_seconds: int = pydantic.Field(
        180,
        ge=6,
        le=43200,
        description="Maximum gap in seconds to interpolate over.",
    )


class ExportConfig(pydantic.BaseModel):
    targets: list[OutputMergingTargetConfig] = pydantic.Field(
        ...,
        description=
        'List of output merging targets. Relies on specifying "campaigns" in the EM27 metadata.'
    )


class Config(pydantic.BaseModel):
    general: GeneralConfig
    profiles: Optional[VerticalProfilesConfig] = None
    proffast: Optional[AutomatedProffastConfig] = None
    export: Optional[ExportConfig] = None

    @staticmethod
    def load(
        path: str = os.path.join(
            tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=3),
            "config",
            "config.json",
        ),
        check_path_existence: bool = True,
    ) -> Config:
        """Load the config file from `config/config.json` (or any given path).

        If `check_path_existence` is set, it will check whether the paths
        specified in the config file exist."""

        assert os.path.isfile(path), f"Config file not found at {path}"
        json_content = tum_esm_utils.files.load_json_file(path)
        assert isinstance(
            json_content, dict
        ), f"Config file at {path} is not dict."
        config = Config(**json_content)

        if check_path_existence:
            for path in [
                config.general.data_src_dirs.datalogger,
                config.general.data_src_dirs.interferograms,
                config.general.data_src_dirs.profiles,
                config.general.data_dst_dirs.results,
                *([] if (config.export is None) else
                  [target.dst_dir for target in config.export.targets])
            ]:
                assert os.path.isdir(path), f"{path} is not a directory."

        if config.profiles is not None:
            assert (
                config.profiles.request_scope.from_date
                <= config.profiles.request_scope.to_date
            )
        if config.proffast is not None:
            assert (
                config.proffast.data_filter.from_date
                <= config.proffast.data_filter.to_date
            )

        return config
