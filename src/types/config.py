from __future__ import annotations
from typing import Literal, Optional
import datetime
import tum_esm_utils
import pydantic
from .basic_types import (
    RetrievalAlgorithm,
    AtmosphericProfileModel,
    SamplingRate,
    OutputTypes,
)


class MetadataConfig(pydantic.BaseModel):
    """GitHub repository where the location data is stored."""

    github_repository: str = pydantic.Field(
        ...,
        pattern=r"^[a-z0-9-_]+/[a-z0-9-_]+$",
        description="GitHub repository name, e.g. `my-org/my-repo`.",
    )

    access_token: Optional[str] = pydantic.Field(
        None,
        min_length=1,
        description=
        "GitHub access token with read access to the repository, only required if the repository is private.",
    )


class DataConfig(pydantic.BaseModel):
    """Location where the input data sourced from."""

    datalogger: tum_esm_utils.validators.StrictDirectoryPath = pydantic.Field(
        ..., description="directory path to datalogger files"
    )
    atmospheric_profiles: tum_esm_utils.validators.StrictDirectoryPath = pydantic.Field(
        ..., description="directory path to atmospheric profile files"
    )
    interferograms: tum_esm_utils.validators.StrictDirectoryPath = pydantic.Field(
        ..., description="directory path to ifg files"
    )
    results: tum_esm_utils.validators.StrictDirectoryPath = pydantic.Field(
        ..., description="directory path to results"
    )


class ProfilesServerConfig(pydantic.BaseModel):
    """Settings for accessing the ccycle ftp server. Besides the
    `email` field, these can be left as default in most cases."""

    email: str = pydantic.Field(
        ...,
        min_length=3,
        description="Email address to use to log in to the ccycle ftp server.",
    )
    max_requests_in_parallel: int = pydantic.Field(
        ...,
        ge=1,
        le=100,
        description=
        "Maximum number of requests to put in the queue on the ccycle server at the same time. Only when a request is finished, a new one can enter the queue.",
    )
    max_requests_per_day: int = pydantic.Field(
        ...,
        ge=1,
        le=1000,
        description="Maximum number of requests to the ccycle server per day.",
    )


class ProfilesScopeConfig(pydantic.BaseModel):
    from_date: datetime.date = pydantic.Field(
        datetime.date(1900, 1, 1),
        description=
        "date in format `YYYY-MM-DD` from which to request vertical profile data.",
    )
    to_date: datetime.date = pydantic.Field(
        datetime.date(2100, 1, 1),
        description=
        "date in format `YYYY-MM-DD` until which to request vertical profile data.",
    )
    models: list[AtmosphericProfileModel] = pydantic.Field(
        ...,
        description="list of data types to request from the ccycle ftp server.",
    )

    @pydantic.model_validator(mode='after')
    def check_date_order(self) -> ProfilesScopeConfig:
        if self.from_date > self.to_date:
            raise ValueError('from_date must be before to_date')
        return self


class ProfilesStandardSitesItemConfig(pydantic.BaseModel):
    identifier: str = pydantic.Field(
        ...,
        description="The identifier on the caltech server",
    )
    lat: float = pydantic.Field(
        ...,
        ge=-90,
        le=90,
    )
    lon: float = pydantic.Field(
        ...,
        ge=-180,
        le=180,
    )
    from_date: datetime.date = pydantic.Field(
        ...,
        description=
        "Date in format `YYYY-MM-DD` from which this standard site is active.",
    )
    to_date: datetime.date = pydantic.Field(
        ...,
        description=
        "Date in format `YYYY-MM-DD` until which this standard site is active.",
    )

    @pydantic.model_validator(mode='after')
    def check_date_order(self) -> ProfilesStandardSitesItemConfig:
        if self.from_date > self.to_date:
            raise ValueError('from_date must be before to_date')
        return self


class RetrievalGeneralConfig(pydantic.BaseModel):
    max_process_count: int = pydantic.Field(
        1,
        ge=1,
        le=128,
        description=
        "How many parallel processes to dispatch. There will be one process per sensor-day. With hyper-threaded CPUs, this can be higher than the number of physical cores.",
    )
    ifg_file_regex: str = pydantic.Field(
        ...,
        min_length=1,
        description=
        "A regex string to match the ifg file names. In this string, `$(SENSOR_ID)` and `$(DATE)` are placeholders for the sensor id and the date of the ifg file.",
        examples=[
            r"^$(SENSOR_ID)$(DATE).*\.\d+$",
            r"^$(SENSOR_ID)$(DATE).*\.nc$",
        ],
    )


class RetrievalIfgFilePermissionsConfig(pydantic.BaseModel):
    """Change the file permissions on the interferogram before the
    retrieval algorithm accesses them. This is done to avoid accidental
    modification of the original interferograms by any retrieval
    algorithm. This is only done for the interferograms files because
    they are not copied into the working directory, but only linked.
    The profiles and datalogger files are copied."""

    fail_on_permission_error: bool = pydantic.Field(
        ...,
        description=
        "Whether to fail if the file permissions cannot be changed. If `False`, a warning will be logged instead.",
    )
    before_processing: Optional[str] = pydantic.Field(
        ...,
        pattern=r"^((r|-)(w|-)(x|-)){3}$",
        description=
        "A unix-like file permission string, e.g. `rwxr-xr-x` - set immediately before running the retrieval algorithm. Only used if not `null`.",
        examples=[
            "rwxr-xr-x",
            "rw-r--r--",
            "rwx------",
        ],
    )
    after_processing: Optional[str] = pydantic.Field(
        ...,
        pattern=r"^((r|-)(w|-)(x|-)){3}$",
        description=
        "A unix-like file permission string, e.g. `rwxr-xr-x`. Set directly after the retrieval algorithm is done. Only used if not `null`.",
        examples=[
            "rwxr-xr-x",
            "rw-r--r--",
            "rwx------",
        ],
    )


class RetrievalJobConfig(pydantic.BaseModel):
    """Settings for filtering the storage data. Only used if `config.data_sources.storage` is `true`."""

    retrieval_algorithm: RetrievalAlgorithm = pydantic.Field(
        ...,
        description=
        "Which retrieval algorithms to use. Proffast 2.2 and 2.3 use the Proffast Pylot under the hood to dispatch it. Proffast 1.0 uses a custom implementation by us similar to the Proffast Pylot."
    )
    atmospheric_profile_model: AtmosphericProfileModel = pydantic.Field(
        ..., description="Which vertical profiles to use for the retrieval."
    )
    sensor_ids: list[str] = pydantic.Field(
        ...,
        min_length=1,
        description="Sensor ids to consider in the retrieval."
    )
    from_date: datetime.date = pydantic.Field(
        ...,
        description=
        "Date string in format `YYYY-MM-DD` from which to consider data in the storage directory."
    )
    to_date: datetime.date = pydantic.Field(
        ...,
        description=
        "Date string in format `YYYY-MM-DD` until which to consider data in the storage directory."
    )

    @pydantic.model_validator(mode='after')
    def check_model_integrity(self) -> RetrievalJobConfig:
        if self.from_date > self.to_date:
            raise ValueError('from_date must be before to_date')
        if self.retrieval_algorithm == "proffast-1.0" and self.atmospheric_profile_model == "GGG2020":
            raise ValueError("proffast-1.0 does not support GGG2020 profiles")
        return self


class GeneralConfig(pydantic.BaseModel):
    metadata: MetadataConfig
    data: DataConfig


class ProfilesConfig(pydantic.BaseModel):
    """Settings for vertical profiles retrieval. If `null`, the vertical profiles script will stop and log a warning"""

    server: ProfilesServerConfig
    scope: ProfilesScopeConfig
    standard_sites: list[ProfilesStandardSitesItemConfig] = pydantic.Field(
        ...,
        description=
        "List of standard sites to request from the ccycle ftp server. The requests for these standard sites are done before any other requests so that data available for these is not rerequested for other sensors.",
    )


class RetrievalConfig(pydantic.BaseModel):
    """Settings for automated proffast processing. If `null`, the automated proffast script will stop and log a warning"""

    general: RetrievalGeneralConfig
    ifg_file_permissions: RetrievalIfgFilePermissionsConfig
    jobs: list[RetrievalJobConfig] = pydantic.Field(
        ...,
        description=
        "List of retrievals to run. The list will be processed sequentially.",
    )


class ExportTargetConfig(pydantic.BaseModel):
    campaign_id: str = pydantic.Field(
        ...,
        description="Campaign specified in location metadata.",
    )
    retrieval_algorithm: RetrievalAlgorithm = pydantic.Field(
        ...,
        description="Which retrieval algorithm used for the retrieval.",
    )
    atmospheric_profile_model: AtmosphericProfileModel = pydantic.Field(
        ...,
        description="Which atmospheric profiles used for the retrieval.",
    )
    data_types: list[OutputTypes] = pydantic.Field(
        ...,
        min_length=1,
        description=
        "Data columns to keep in the merged output files. The columns will be prefixed with the sensor id, i.e. `$(SENSOR_ID)_$(COLUMN_NAME)`.",
    )
    sampling_rate: SamplingRate = pydantic.Field(
        ...,
        description="Interval of resampled data.",
    )
    max_interpolation_gap_seconds: int = pydantic.Field(
        180,
        ge=6,
        le=43200,
        description="Maximum gap in seconds to interpolate over.",
    )
    dst_dir: tum_esm_utils.validators.StrictDirectoryPath = pydantic.Field(
        ...,
        description="Directory to write the output to.",
    )


class Config(pydantic.BaseModel):
    version: Literal["1.0"] = pydantic.Field(
        ...,
        description=
        "Version of the retrieval pipeline which is compatible with this config file. Retrievals done with any version `1.x` will produce the same output files as retrievals done with version `1.0`. But higher version numbers might use a different config file structure and produce more output files."
    )
    general: GeneralConfig
    profiles: Optional[ProfilesConfig] = None
    retrieval: Optional[RetrievalConfig] = None
    export_targets: Optional[list[ExportTargetConfig]] = pydantic.Field(
        None,
        description=
        'List of output merging targets. Relies on specifying "campaigns" in the EM27 metadata.'
    )

    @staticmethod
    def load(
        path: str = tum_esm_utils.files.
        rel_to_abs_path("../../config/config.json"),
        ignore_path_existence: bool = False,
    ) -> Config:
        """Load the config file from `config/config.json` (or any given path).

        If `check_path_existence` is set, it will check whether the paths
        specified in the config file exist."""

        with open(path, 'r') as f:
            return Config.model_validate_json(
                f.read(),
                context={"ignore-path-existence": ignore_path_existence},
            )
