from __future__ import annotations

import datetime
import os
from typing import Literal, Optional

import dotenv
import pydantic
import tum_esm_utils

from .basic_types import AtmosphericProfileModel, RetrievalAlgorithm


class MetadataConfig(pydantic.BaseModel):
    """GitHub repository where the location data is stored."""

    model_config = pydantic.ConfigDict(extra="forbid")

    github_repository: str = pydantic.Field(
        ...,
        pattern=r"^[a-z0-9-_]+/[a-z0-9-_]+$",
        description="GitHub repository name, e.g. `my-org/my-repo`.",
    )
    access_token: Optional[str] = pydantic.Field(
        None,
        min_length=1,
        description="GitHub access token with read access to the repository, only required if the repository is private.",
    )


class GroundPressureConfig(pydantic.BaseModel):
    """Format of the ground pressure files. We support any text file that stores one data point per row and separates the columns with a comma, space, or tab, i.e. CSV, TSV, or space-separated files. Using the `file_regex` field, you specify which files to consider for a given sensor id and date.

    You have to specify the columns that contain the date and time of the data. There is three options to specify this - the CLI will complain if you configure none or more than one of these options:

    * One column with a datetime string -> configure `datetime_column` and `datetime_column_format`
    * Two columns, one with the date and one with the time -> configure `date_column`, `date_column_format`, `time_column`, and `time_column_format`
    * One column with a unix timestamp -> configure `unix_timestamp_column` and `unix_timestamp_column_format`"""

    model_config = pydantic.ConfigDict(extra="forbid")

    # where to find the files
    path: tum_esm_utils.validators.StrictDirectoryPath = pydantic.Field(
        ...,
        description="Directory path to ground pressure files.",
    )

    # how to find and parse the files
    file_regex: str = pydantic.Field(
        ...,
        min_length=1,
        description=(
            "A regex string to match the ground pressure file names. In this string, you can use the placeholders `$(SENSOR_ID)`, `$(YYYY)`, `$(YY)`, `$(MM)`, and `$(DD)` to make this regex target a certain station and date. The placeholder `$(DATE)` is a shortcut for `$(YYYY)$(MM)$(DD)`."
        ),
        examples=[
            "^$(DATE).tsv$",
            "^$(SENSOR_ID)_$(DATE).dat$",
            "^ground-pressure-$(SENSOR_ID)-$(YYYY)-$(MM)-$(DD).csv$",
        ],
    )
    separator: str = pydantic.Field(
        ...,
        description="Separator used in the ground pressure files. Only needed and used if the file format is `text`.",
        min_length=1,
        max_length=1,
        examples=[",", "\t", " ", ";"],
    )

    # one datetime column
    datetime_column: Optional[str] = pydantic.Field(
        None,
        description="Column name in the ground pressure files that contains the datetime.",
        examples=["datetime", "dt", "utc-datetime"],
    )
    datetime_column_format: Optional[str] = pydantic.Field(
        None,
        description="Format of the datetime column in the ground pressure files.",
        examples=["%Y-%m-%dT%H:%M:%S"],
    )

    # two columns for date and time
    date_column: Optional[str] = pydantic.Field(
        None,
        description="Column name in the ground pressure files that contains the date.",
        examples=["date", "d", "utc-date"],
    )
    date_column_format: Optional[str] = pydantic.Field(
        None,
        description="Format of the date column in the ground pressure files.",
        examples=["%Y-%m-%d", "%Y%m%d", "%d.%m.%Y"],
    )
    time_column: Optional[str] = pydantic.Field(
        None,
        description="Column name in the ground pressure files that contains the time.",
        examples=["time", "t", "utc-time"],
    )
    time_column_format: Optional[str] = pydantic.Field(
        None,
        description="Format of the time column in the ground pressure files.",
        examples=["%H:%M:%S", "%H:%M", "%H%M%S"],
    )

    # one unix timestamp column
    unix_timestamp_column: Optional[str] = pydantic.Field(
        None,
        description="Column name in the ground pressure files that contains the unix timestamp.",
        examples=["unix-timestamp", "timestamp", "ts"],
    )
    unix_timestamp_column_format: Optional[Literal["s", "ms", "us", "ns"]] = pydantic.Field(
        None,
        description="Format of the unix timestamp column in the ground pressure files. I.e. is the Unix timestamp in seconds, milliseconds, etc.?",
    )

    # pressure column
    pressure_column: str = pydantic.Field(
        ...,
        description="Column name in the ground pressure files that contains the pressure.",
        examples=["pressure", "p", "ground_pressure"],
    )
    pressure_column_format: Literal["hPa", "Pa", "bar", "mbar", "atm", "psi", "inHg", "mmHg"] = (
        pydantic.Field(
            ...,
            description="Unit of the pressure column in the ground pressure files.",
        )
    )

    # validate -> you can only set either date AND time OR unix_timestamp
    @pydantic.model_validator(mode="after")
    def _check_datetime_columns(self) -> GroundPressureConfig:
        required = {
            "datetime_column": [],
            "date_column": ["time_column"],
            "time_column": ["date_column"],
            "unix_timestamp_column": [],
        }
        forbidden = {
            "datetime_column": ["date_column", "time_column", "unix_timestamp_column"],
            "date_column": ["datetime_column", "unix_timestamp_column"],
            "time_column": ["datetime_column", "unix_timestamp_column"],
            "unix_timestamp_column": ["datetime_column", "date_column", "time_column"],
        }

        for col in ["datetime_column", "date_column", "time_column", "unix_timestamp_column"]:
            fmt = col + "_format"
            if (getattr(self, col) is not None) and (getattr(self, fmt) is None):
                raise ValueError(f"You have to set `{fmt}` if you set `{col}`")
            if (getattr(self, fmt) is not None) and (getattr(self, col) is None):
                raise ValueError(f"You have to set `{col}` if you set `{fmt}`")

            if getattr(self, col) is not None:
                for other_col in required[col]:
                    if getattr(self, other_col) is None:
                        raise ValueError(f"You have to set `{other_col}` if you set `{col}`")
                for other_col in forbidden[col]:
                    if getattr(self, other_col) is not None:
                        raise ValueError(f"You cannot set `{other_col}` if you set `{col}`")

        return self


class DataConfig(pydantic.BaseModel):
    """Location where the input data sourced from."""

    model_config = pydantic.ConfigDict(extra="forbid")

    ground_pressure: GroundPressureConfig = pydantic.Field(
        ...,
        description="directory path and format configuration of the ground pressure files",
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

    model_config = pydantic.ConfigDict(extra="forbid")

    email: str = pydantic.Field(
        ...,
        min_length=3,
        description="Email address to use to log in to the ccycle ftp server.",
    )
    max_parallel_requests: int = pydantic.Field(
        ...,
        ge=1,
        le=200,
        description="Maximum number of requests to put in the queue on the ccycle server at the same time. Only when a request is finished, a new one can enter the queue.",
    )


class ProfilesScopeConfig(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")

    from_date: datetime.date = pydantic.Field(
        datetime.date(1900, 1, 1),
        description="Date in format `YYYY-MM-DD` from which to request vertical profile data.",
    )
    to_date: datetime.date = pydantic.Field(
        datetime.date(2100, 1, 1),
        description="Date in format `YYYY-MM-DD` until which to request vertical profile data.",
    )
    models: list[AtmosphericProfileModel] = pydantic.Field(
        ...,
        description="list of data types to request from the ccycle ftp server.",
    )

    @pydantic.model_validator(mode="after")
    def check_date_order(self) -> ProfilesScopeConfig:
        if self.from_date > self.to_date:
            raise ValueError("from_date must be before to_date")
        return self


class ProfilesGGG2020StandardSitesItemConfig(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")

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
        description="Date in format `YYYY-MM-DD` from which this standard site is active.",
    )
    to_date: datetime.date = pydantic.Field(
        default_factory=lambda: datetime.date.today() - datetime.timedelta(days=1),
        description="Date in format `YYYY-MM-DD` until which this standard site is active.",
    )

    @pydantic.model_validator(mode="after")
    def check_date_order(self) -> ProfilesGGG2020StandardSitesItemConfig:
        if self.from_date > self.to_date:
            raise ValueError("from_date must be before to_date")
        return self


class RetrievalGeneralConfig(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")

    max_process_count: int = pydantic.Field(
        1,
        ge=1,
        le=128,
        description="How many parallel processes to dispatch. There will be one process per sensor-day. With hyper-threaded CPUs, this can be higher than the number of physical cores.",
    )
    ifg_file_regex: str = pydantic.Field(
        ...,
        min_length=1,
        description="A regex string to match the ifg file names. In this string, `$(SENSOR_ID)`, `$(YYYY)`, `$(YY)`, `$(MM)`, and `$(DD)` are placeholders to target a certain station and date. The placeholder `$(DATE)` is a shortcut for `$(YYYY)$(MM)$(DD)`. They don't have to be used - you can also run the retrieval on any file it finds in the directory using `.*`",
        examples=[
            r"^*\.\d+$" r"^$(SENSOR_ID)$(DATE).*\.\d+$",
            r"^$(SENSOR_ID)-$(YYYY)-$(MM)-$(DD).*\.nc$",
        ],
    )
    queue_verbosity: Literal["compact", "verbose"] = pydantic.Field(
        "compact",
        description="How much information the retrieval queue should print out. In `verbose` mode it will print out the full list of sensor-days for each step of the filtering process. This can help when figuring out why a certain sensor-day is not processed.",
    )
    container_dir: Optional[str] = pydantic.Field(
        None,
        description="Directory to store the containers in. If not set, it will use `./data/containers` inside the pipeline directory.",
    )


class RetrievalJobSettingsILSConfig(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")

    channel1_me: float = pydantic.Field(...)
    channel1_pe: float = pydantic.Field(...)
    channel2_me: float = pydantic.Field(...)
    channel2_pe: float = pydantic.Field(...)


class RetrievalJobSettingsConfig(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")

    store_binary_spectra: bool = pydantic.Field(
        False,
        description="Whether to store the binary spectra files. These are the files that are used by the retrieval algorithm. They are not needed for the output files, but can be useful for debugging.",
    )
    dc_min_threshold: float = pydantic.Field(
        0.05,
        ge=0.001,
        le=0.999,
        description="Value used for the `DC_min` threshold in Proffast. If not set, defaults to the Proffast default.",
    )
    dc_var_threshold: float = pydantic.Field(
        0.10,
        ge=0.001,
        le=0.999,
        description="Value used for the `DC_var` threshold in Proffast. If not set, defaults to the Proffast default.",
    )
    use_local_pressure_in_pcxs: bool = pydantic.Field(
        False,
        description="Whether to use the local pressure in the pcxs files. If not used, it will tell PCXS to use the pressure from the atmospheric profiles (set the input value in the `.inp` file to `9999.9`). If used, the pipeline computes the solar noon time using `skyfield` and averages the local pressure over the time period noon-2h to noon+2h.",
    )
    use_ifg_corruption_filter: bool = pydantic.Field(
        True,
        description="Whether to use the ifg corruption filter. This filter is a program based on `preprocess4` and is part of the `tum-esm-utils` library: https://tum-esm-utils.netlify.app/api-reference#tum_esm_utilsinterferograms. If activated, we will only pass the interferograms to the retrieval algorithm that pass the filter - i.e. that won't cause it to crash.",
    )
    custom_ils: dict[str, RetrievalJobSettingsILSConfig] = pydantic.Field(
        {},
        description="Maps sensor IDS to ILS correction values. If not set, the pipeline will use the values published inside the Proffast Pylot codebase (https://gitlab.eudat.eu/coccon-kit/proffastpylot/-/blob/master/prfpylot/ILSList.csv?ref_type=heads).",
    )
    output_suffix: Optional[str] = pydantic.Field(
        None,
        description="Suffix to append to the output folders. If not set, the pipeline output folders are named `sensorid/YYYYMMDD/`. If set, the folders are named `sensorid/YYYYMMDD_suffix/`. This is useful when having multiple retrieval jobs processing the same sensor dates with different settings.",
    )
    pressure_calibration_factors: dict[str, float] = pydantic.Field(
        {},
        description="Maps sensor IDS to pressure calibration factors. If not set, it is set to 1 for each sensor. `corrected_pressure = input_pressure * calibration_factor + calibration_offset`",
        examples=['{"ma": 0.99981}', '{"ma": 1.00019, "mb": 0.99981}'],
    )
    pressure_calibration_offsets: dict[str, float] = pydantic.Field(
        {},
        description="Maps sensor IDS to pressure calibration offsets. If not set, it is set to 0 for each sensor. `corrected_pressure = input_pressure * calibration_factor + calibration_offset`",
        examples=['{"ma": -0.00007}', '{"ma": -0.00007, "mb": 0.00019}'],
    )


class RetrievalJobConfig(pydantic.BaseModel):
    """Settings for filtering the storage data. Only used if `config.data_sources.storage` is `true`."""

    model_config = pydantic.ConfigDict(extra="forbid")

    retrieval_algorithm: RetrievalAlgorithm = pydantic.Field(
        ...,
        description="Which retrieval algorithms to use. Proffast 2.X uses the Proffast Pylot under the hood to dispatch it. Proffast 1.0 uses a custom implementation by us similar to the Proffast Pylot.",
    )
    atmospheric_profile_model: AtmosphericProfileModel = pydantic.Field(
        ..., description="Which vertical profiles to use for the retrieval."
    )
    sensor_ids: list[str] = pydantic.Field(
        ..., min_length=1, description="Sensor ids to consider in the retrieval."
    )
    from_date: datetime.date = pydantic.Field(
        ...,
        description="Date string in format `YYYY-MM-DD` from which to consider data in the storage directory.",
    )
    to_date: datetime.date = pydantic.Field(
        default_factory=lambda: datetime.date.today() - datetime.timedelta(days=1),
        description="Date string in format `YYYY-MM-DD` until which to consider data in the storage directory.",
    )
    settings: RetrievalJobSettingsConfig = pydantic.Field(
        RetrievalJobSettingsConfig(),
        description="Advanced settings that only apply to this retrieval job",
    )

    @pydantic.model_validator(mode="after")
    def check_model_integrity(self) -> RetrievalJobConfig:
        if self.from_date > self.to_date:
            raise ValueError("from_date must be before to_date")
        if (
            self.retrieval_algorithm == "proffast-1.0"
            and self.atmospheric_profile_model == "GGG2020"
        ):
            raise ValueError("proffast-1.0 does not support GGG2020 profiles")
        return self


class GeneralConfig(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")
    metadata: Optional[MetadataConfig] = pydantic.Field(
        None,
        description="If not set, the pipeline will use local metadata files or abort if the local files are not found. If local files are found, they will always be preferred over the remote data even if the remote source is configured.",
    )
    data: DataConfig


class ProfilesConfig(pydantic.BaseModel):
    """Settings for vertical profiles retrieval. If `null`, the vertical profiles script will stop and log a warning"""

    model_config = pydantic.ConfigDict(extra="forbid")

    server: ProfilesServerConfig
    scope: Optional[ProfilesScopeConfig] = pydantic.Field(
        None,
        description="Scope of the vertical profiles to request from the ccycle ftp server. If set to `null`, the script will not request any vertical profiles besides the configured standard sites.",
    )
    GGG2020_standard_sites: list[ProfilesGGG2020StandardSitesItemConfig] = pydantic.Field(
        ...,
        description="List of standard sites to request from the ccycle ftp server. The requests for these standard sites are done before any other requests so that data available for these is not rerequested for other sensors. See https://tccon-wiki.caltech.edu/Main/ObtainingGinputData#Requesting_to_be_added_as_a_standard_site for more information.",
    )


class RetrievalConfig(pydantic.BaseModel):
    """Settings for automated proffast processing. If `null`, the automated proffast script will stop and log a warning"""

    model_config = pydantic.ConfigDict(extra="forbid")

    general: RetrievalGeneralConfig
    jobs: list[RetrievalJobConfig] = pydantic.Field(
        ...,
        description="List of retrievals to run. The list will be processed sequentially.",
    )


class BundleTargetConfig(pydantic.BaseModel):
    """There will be one file per sensor id and atmospheric profile and retrieval algorithm combination.

    The final name looks like `em27-retrieval-bundle-$SENSOR_ID-$RETRIEVAL_ALGORITHM-$ATMOSPHERIC_PROFILE-$FROM_DATE-$TO_DATE$BUNDLE_SUFFIX.$OUTPUT_FORMAT`, e.g.`em27-retrieval-bundle-ma-GGG2020-proffast-2.4-20150801-20240523-v2.1.csv`. The bundle suffix is optional and can be used to distinguish between different
    internal datasets."""

    model_config = pydantic.ConfigDict(extra="forbid")

    dst_dir: tum_esm_utils.validators.StrictDirectoryPath = pydantic.Field(
        ...,
        description="Directory to write the bundeled outputs to.",
    )
    output_formats: list[Literal["csv", "parquet"]] = pydantic.Field(
        ...,
        description="List of output formats to write the merged output files in.",
    )
    from_datetime: datetime.datetime = pydantic.Field(
        ..., description="Date in format `YYYY-MM-DDTHH:MM:SS` from which to bundle data"
    )
    to_datetime: datetime.datetime = pydantic.Field(
        ..., description="Date in format `YYYY-MM-DDTHH:MM:SS` to which to bundle data"
    )
    retrieval_algorithms: list[RetrievalAlgorithm] = pydantic.Field(
        ..., description="The retrieval algorithms for which to bundle the outputs"
    )
    atmospheric_profile_models: list[AtmosphericProfileModel] = pydantic.Field(
        ..., description="The atmospheric profile models for which to bundle the outputs"
    )
    sensor_ids: list[str] = pydantic.Field(
        ..., description="The sensor ids for which to bundle the outputs"
    )
    bundle_suffix: Optional[str] = pydantic.Field(
        None,
        description="Suffix to append to the output bundles.",
        min_length=1,
        examples=["v2.1", "v2.2", "oco2-gradient-paper-2021"],
    )
    retrieval_job_output_suffix: Optional[str] = pydantic.Field(
        None,
        description="When you ran the retrieval with a custom suffix, you can specify it here to only bundle the outputs of this suffix. Use the same value here as in the field `config.retrieval.jobs[i].settings.output_suffix`.",
    )
    parse_dc_timeseries: bool = pydantic.Field(
        False,
        description="Whether to parse the DC timeseries from the results directories. This is an output only available in this Pipeline for Proffast2.4. We adapted the preprocessor to output the DC min/mean/max/variation values for each record of data. If you having issues with a low signal intensity on one or both channels, you can run the retrieval with a very low DC_min threshold and filter the data afterwards instead of having to rerun the retrieval.",
    )


class Config(pydantic.BaseModel):
    """A pydantic model describing the config file schema."""

    model_config = pydantic.ConfigDict(extra="forbid")

    version: Literal["1.5"] = pydantic.Field(
        ...,
        description="Version of the retrieval pipeline which is compatible with this config file. Retrievals done with any version `1.x` will produce the same output files as retrievals done with version `1.0`. But higher version numbers might use a different config file structure and produce more output files.",
    )
    general: GeneralConfig
    profiles: Optional[ProfilesConfig] = None
    retrieval: Optional[RetrievalConfig] = None
    bundles: Optional[list[BundleTargetConfig]] = pydantic.Field(
        None, description="List of output bundling targets."
    )

    @staticmethod
    def get_config_dir() -> str:
        """Get config/metadata directory path from environment variable if set.

        If not set, returns default config directory path inside the repository."""

        env_path = os.path.join(tum_esm_utils.files.rel_to_abs_path("../../config"), ".env")
        if os.path.isfile(env_path):
            dotenv.load_dotenv(env_path)
        return os.getenv("ERP_CONFIG_DIR", tum_esm_utils.files.rel_to_abs_path("../../config"))

    @staticmethod
    def get_config_path() -> str:
        """Get config file path from environment variable if set.

        If not set, returns default config file path inside the repository."""

        return os.path.join(Config.get_config_dir(), "config.json")

    @staticmethod
    def load(
        path: Optional[str] = None,
        ignore_path_existence: bool = False,
    ) -> Config:
        """Load the config file from `config/config.json` (or any given path).

        If `check_path_existence` is set, it will check whether the paths
        specified in the config file exist."""

        if path is None:
            path = Config.get_config_path()

        with open(path, "r") as f:
            return Config.model_validate_json(
                f.read(),
                context={"ignore-path-existence": ignore_path_existence},
            )
