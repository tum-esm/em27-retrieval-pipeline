from __future__ import annotations
from typing import Literal, Optional, Union
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
    max_parallel_requests: int = pydantic.Field(
        ...,
        ge=1,
        le=200,
        description=
        "Maximum number of requests to put in the queue on the ccycle server at the same time. Only when a request is finished, a new one can enter the queue.",
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


class ProfilesGGG2020StandardSitesItemConfig(pydantic.BaseModel):
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
    def check_date_order(self) -> ProfilesGGG2020StandardSitesItemConfig:
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


class RetrievalJobSettingsILSConfig(pydantic.BaseModel):
    channel1_me: float = pydantic.Field(...)
    channel1_pe: float = pydantic.Field(...)
    channel2_me: float = pydantic.Field(...)
    channel2_pe: float = pydantic.Field(...)


class RetrievalJobSettingsConfig(pydantic.BaseModel):
    store_binary_spectra: bool = pydantic.Field(
        False,
        description=
        "Whether to store the binary spectra files. These are the files that are used by the retrieval algorithm. They are not needed for the output files, but can be useful for debugging.",
    )
    dc_min_threshold: float = pydantic.Field(
        0.05,
        ge=0.001,
        le=0.999,
        description=
        "Value used for the `DC_min` threshold in Proffast. If not set, defaults to the Proffast default.",
    )
    dc_var_threshold: float = pydantic.Field(
        0.10,
        ge=0.001,
        le=0.999,
        description=
        "Value used for the `DC_var` threshold in Proffast. If not set, defaults to the Proffast default.",
    )
    use_local_pressure_in_pcxs: bool = pydantic.Field(
        False,
        description=
        "Whether to use the local pressure in the pcxs files. If not used, it will tell PCXS to use the pressure from the atmospheric profiles (set the input value in the `.inp` file to `9999.9`). If used, the pipeline computes the solar noon time using `skyfield` and averages the local pressure over the time period noon-2h to noon+2h.",
    )
    use_ifg_corruption_filter: bool = pydantic.Field(
        True,
        description=
        "Whether to use the ifg corruption filter. This filter is a program based on `preprocess4` and is part of the `tum-esm-utils` library: https://tum-esm-utils.netlify.app/api-reference#tum_esm_utilsinterferograms. If activated, we will only pass the interferograms to the retrieval algorithm that pass the filter - i.e. that won't cause it to crash.",
    )
    custom_ils: Optional[
        dict[str, RetrievalJobSettingsILSConfig]
    ] = pydantic.Field(
        None,
        description=
        "Maps sensor IDS to ILS correction values. If not set, the pipeline will use the values published inside the Proffast Pylot codebase (https://gitlab.eudat.eu/coccon-kit/proffastpylot/-/blob/master/prfpylot/ILSList.csv?ref_type=heads).",
    )
    output_suffix: Optional[str] = pydantic.Field(
        None,
        description=
        "Suffix to append to the output folders. If not set, the pipeline output folders are named `sensorid/YYYYMMDD/`. If set, the folders are named `sensorid/YYYYMMDD_suffix/`. This is useful when having multiple retrieval jobs processing the same sensor dates with different settings.",
    )


class RetrievalJobConfig(pydantic.BaseModel):
    """Settings for filtering the storage data. Only used if `config.data_sources.storage` is `true`."""

    retrieval_algorithm: RetrievalAlgorithm = pydantic.Field(
        ...,
        description=
        "Which retrieval algorithms to use. Proffast 2.X uses the Proffast Pylot under the hood to dispatch it. Proffast 1.0 uses a custom implementation by us similar to the Proffast Pylot."
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
    settings: RetrievalJobSettingsConfig = pydantic.Field(
        RetrievalJobSettingsConfig(),
        description="Advanced settings that only apply to this retrieval job"
    )

    @pydantic.model_validator(mode='after')
    def check_model_integrity(self) -> RetrievalJobConfig:
        if self.from_date > self.to_date:
            raise ValueError('from_date must be before to_date')
        if self.retrieval_algorithm == "proffast-1.0" and self.atmospheric_profile_model == "GGG2020":
            raise ValueError("proffast-1.0 does not support GGG2020 profiles")
        return self


class GeneralConfig(pydantic.BaseModel):
    metadata: Optional[MetadataConfig] = pydantic.Field(
        None,
        description=
        "If not set, the pipeline will use local metadata files or abort if the local files are not found. If local files are found, they will always be preferred over the remote data even if the remote source is configured.",
    )
    data: DataConfig


class ProfilesConfig(pydantic.BaseModel):
    """Settings for vertical profiles retrieval. If `null`, the vertical profiles script will stop and log a warning"""

    server: ProfilesServerConfig
    scope: Optional[ProfilesScopeConfig] = pydantic.Field(
        None,
        description=
        "Scope of the vertical profiles to request from the ccycle ftp server. If set to `null`, the script will not request any vertical profiles besides the configured standard sites.",
    )
    GGG2020_standard_sites: list[
        ProfilesGGG2020StandardSitesItemConfig
    ] = pydantic.Field(
        ...,
        description=
        "List of standard sites to request from the ccycle ftp server. The requests for these standard sites are done before any other requests so that data available for these is not rerequested for other sensors. See https://tccon-wiki.caltech.edu/Main/ObtainingGinputData#Requesting_to_be_added_as_a_standard_site for more information.",
    )


class RetrievalConfig(pydantic.BaseModel):
    """Settings for automated proffast processing. If `null`, the automated proffast script will stop and log a warning"""

    general: RetrievalGeneralConfig
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
    """A pydantic model describing the config file schema."""

    version: Literal["1.3"] = pydantic.Field(
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
        path: Union[str, None] = None,
        ignore_path_existence: bool = False,
    ) -> Config:
        """Load the config file from `config/config.json` (or any given path).

        If `check_path_existence` is set, it will check whether the paths
        specified in the config file exist."""

        if path is None:
            path = tum_esm_utils.files.rel_to_abs_path("../../config/config.json")

        with open(path, 'r') as f:
            return Config.model_validate_json(
                f.read(),
                context={"ignore-path-existence": ignore_path_existence},
            )
