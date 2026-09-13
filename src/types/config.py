from __future__ import annotations

import datetime
import os
from typing import Any, Literal, Optional

import dotenv
import pydantic
import tomli
import tum_esm_utils

from ..em27_metadata import toml as toml_utils
from .basic_types import (
    DATE_STRING_PATTERN,
    UTC_DATETIME_STRING_PATTERN,
    AtmosphericProfileModel,
    RetrievalAlgorithm,
    parse_date_string,
    parse_datetime_string,
)
from .old_schemas import OldConfig


class MetadataConfig(pydantic.BaseModel):
    """How and where to get the metadata from."""

    model_config = pydantic.ConfigDict(extra="forbid")

    source: Literal["local", "github"] = pydantic.Field(
        ...,
        description="Where to source the metadata from. If `local`, it will use `config/em27_metadata.toml`. If `github`, it will download the metadata from the GitHub repository specified in the `github_repository` field.",
    )
    github_repository: Optional[str] = pydantic.Field(
        default=None,
        pattern=r"^[a-z0-9-_]+/[a-z0-9-_]+$",
        description="GitHub repository name, e.g. `my-org/my-repo`.",
    )
    github_access_token: Optional[str] = pydantic.Field(
        default=None,
        min_length=1,
        description="GitHub access token with read access to the repository, only required if the repository is private.",
    )

    @pydantic.model_validator(mode="after")
    def check_github_repository(self) -> MetadataConfig:
        if self.source == "github" and (self.github_repository is None):
            raise ValueError("You have to set `github_repository` if you set `source` to `github`")
        return self


class DataSubConfigs:
    class GroundPressure(pydantic.BaseModel):
        """Format of the ground pressure files. We support any text file that stores one data point per row and separates the columns with a comma, space, or tab, i.e. CSV, TSV, or space-separated files. Using the `file_regex` field, you specify which files to consider for a given sensor id and date.

        You have to specify the columns that contain the date and time of the data. There is three options to specify this - the CLI will complain if you configure none or more than one of these options:

        * One column with a datetime string -> configure `datetime_column` and `datetime_column_format`
        * Two columns, one with the date and one with the time -> configure `date_column`, `date_column_format`, `time_column`, and `time_column_format`
        * One column with a unix timestamp -> configure `unix_timestamp_column` and `unix_timestamp_column_format`"""

        model_config = pydantic.ConfigDict(extra="forbid")

        # where to find the files
        path: tum_esm_utils.validators.StrictDirectoryPath = pydantic.Field(
            ...,
            description="Directory path to ground pressure files. You should use absolute paths, but if you need relative paths, then this is relative to the caller of the CLI or the pipeline's entrypoint.",
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
            default=None,
            description="Column name in the ground pressure files that contains the datetime.",
            examples=["datetime", "dt", "utc-datetime"],
        )
        datetime_column_format: Optional[str] = pydantic.Field(
            default=None,
            description="Format of the datetime column in the ground pressure files.",
            examples=["%Y-%m-%dT%H:%M:%S"],
        )

        # two columns for date and time
        date_column: Optional[str] = pydantic.Field(
            default=None,
            description="Column name in the ground pressure files that contains the date.",
            examples=["date", "d", "utc-date"],
        )
        date_column_format: Optional[str] = pydantic.Field(
            default=None,
            description="Format of the date column in the ground pressure files.",
            examples=["%Y-%m-%d", "%Y%m%d", "%d.%m.%Y"],
        )
        time_column: Optional[str] = pydantic.Field(
            default=None,
            description="Column name in the ground pressure files that contains the time.",
            examples=["time", "t", "utc-time"],
        )
        time_column_format: Optional[str] = pydantic.Field(
            default=None,
            description="Format of the time column in the ground pressure files.",
            examples=["%H:%M:%S", "%H:%M", "%H%M%S"],
        )

        # one unix timestamp column
        unix_timestamp_column: Optional[str] = pydantic.Field(
            default=None,
            description="Column name in the ground pressure files that contains the unix timestamp.",
            examples=["unix-timestamp", "timestamp", "ts"],
        )
        unix_timestamp_column_format: Optional[Literal["s", "ms", "us", "ns"]] = pydantic.Field(
            default=None,
            description="Format of the unix timestamp column in the ground pressure files. I.e. is the Unix timestamp in seconds, milliseconds, etc.?",
        )

        # pressure column
        pressure_column: str = pydantic.Field(
            ...,
            description="Column name in the ground pressure files that contains the pressure.",
            examples=["pressure", "p", "ground_pressure"],
        )
        pressure_column_format: Literal[
            "hPa", "Pa", "bar", "mbar", "atm", "psi", "inHg", "mmHg"
        ] = pydantic.Field(
            ...,
            description="Unit of the pressure column in the ground pressure files.",
        )

        # before the validation, if the path is relative, make it absolute based on the cwd
        @pydantic.model_validator(mode="before")
        def _make_path_absolute(cls, values: Any) -> Any:
            if isinstance(values["path"], str):
                if not os.path.isabs(values["path"]):
                    values["path"] = os.path.abspath(values["path"])
            return values

        # validate -> you can only set either date AND time OR unix_timestamp
        @pydantic.model_validator(mode="after")
        def _check_datetime_columns(self) -> DataSubConfigs.GroundPressure:
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

    class Interferograms(pydantic.BaseModel):
        """Where to find the interferograms."""

        path: tum_esm_utils.validators.StrictDirectoryPath = pydantic.Field(
            ...,
            description="Directory path to atmospheric profile files. You should use absolute paths, but if you need relative paths, then this is relative to the caller of the CLI or the pipeline's entrypoint.",
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

        # before the validation, if the path is relative, make it absolute based on the cwd
        @pydantic.model_validator(mode="before")
        def _make_path_absolute(cls, values: Any) -> Any:
            assert isinstance(values["path"], str)
            if not os.path.isabs(values["path"]):
                values["path"] = os.path.abspath(values["path"])
            return values

    class AtmosphericProfiles(pydantic.BaseModel):
        """Where to find the atmospheric profile files."""

        path: tum_esm_utils.validators.StrictDirectoryPath = pydantic.Field(
            ...,
            description="Directory path to atmospheric profile files. You should use absolute paths, but if you need relative paths, then this is relative to the caller of the CLI or the pipeline's entrypoint.",
        )

        # before the validation, if the path is relative, make it absolute based on the cwd
        @pydantic.model_validator(mode="before")
        def _make_path_absolute(cls, values: Any) -> Any:
            assert isinstance(values["path"], str)
            if not os.path.isabs(values["path"]):
                values["path"] = os.path.abspath(values["path"])
            return values

    class Results(pydantic.BaseModel):
        """Where to find the results."""

        path: tum_esm_utils.validators.StrictDirectoryPath = pydantic.Field(
            ...,
            description="Directory path to atmospheric profile files. You should use absolute paths, but if you need relative paths, then this is relative to the caller of the CLI or the pipeline's entrypoint.",
        )

        # before the validation, if the path is relative, make it absolute based on the cwd
        @pydantic.model_validator(mode="before")
        def _make_path_absolute(cls, values: Any) -> Any:
            assert isinstance(values["path"], str)
            if not os.path.isabs(values["path"]):
                values["path"] = os.path.abspath(values["path"])
            return values


class DataConfig(pydantic.BaseModel):
    """Location where the input data sourced from."""

    model_config = pydantic.ConfigDict(extra="forbid")

    atmospheric_profiles: DataSubConfigs.AtmosphericProfiles = pydantic.Field(...)
    ground_pressure: DataSubConfigs.GroundPressure = pydantic.Field(...)
    interferograms: DataSubConfigs.Interferograms = pydantic.Field(...)
    results: DataSubConfigs.Results = pydantic.Field(...)


class GGGProfilesDownloaderSubConfigs:
    class Server(pydantic.BaseModel):
        """Settings for accessing the ccycle ftp server. Besides the
        `email` field, these can be left as default in most cases."""

        model_config = pydantic.ConfigDict(extra="forbid")

        email: str = pydantic.Field(
            ...,
            min_length=3,
            description="Email address to use to log in to the ccycle ftp server.",
        )
        max_parallel_requests: int = pydantic.Field(
            default=25,
            ge=1,
            le=200,
            description="Maximum number of requests to put in the queue on the ccycle server at the same time. Only when a request is finished, a new one can enter the queue.",
        )

    class Scope(pydantic.BaseModel):
        """From when to when to request the vertical profile data and which models to request. It use the em27 metadata to determine which sensors are located at which locations and request all profiles for these locations in the period specified in this scope."""

        model_config = pydantic.ConfigDict(extra="forbid")

        from_date: str = pydantic.Field(
            "1900-01-01",
            pattern=DATE_STRING_PATTERN,
            description="Date in format `YYYY-MM-DD` from which to request vertical profile data.",
        )
        to_date: str = pydantic.Field(
            "2100-01-01",
            pattern=DATE_STRING_PATTERN,
            description="Date in format `YYYY-MM-DD` until which to request vertical profile data.",
        )
        models: list[AtmosphericProfileModel] = pydantic.Field(
            ...,
            description="list of data types to request from the ccycle ftp server.",
        )
        force_download_locations: list[str] = pydantic.Field(
            default=[],
            description="List of locations to force-download data for. These will be downloaded even at times where no instrument in the metadata is located there.",
        )

        @pydantic.model_validator(mode="after")
        def check_date_order(self) -> GGGProfilesDownloaderSubConfigs.Scope:
            if self.from_date_parsed > self.to_date_parsed:
                raise ValueError("from_date must be before to_date")
            return self

        @property
        def from_date_parsed(self) -> datetime.date:
            return parse_date_string(self.from_date)

        @property
        def to_date_parsed(self) -> datetime.date:
            return parse_date_string(self.to_date)

    class GGG2020StandardSitesItem(pydantic.BaseModel):
        """A list item of the `ggg2020_standard_sites` list describing for which standard site to download data for."""

        model_config = pydantic.ConfigDict(extra="forbid")

        identifier: str = pydantic.Field(
            ...,
            min_length=1,
            description="Identifier of the standard site used on the ginput server.",
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
        from_date: str = pydantic.Field(
            ...,
            pattern=DATE_STRING_PATTERN,
            description="Date in format `YYYY-MM-DD` from which this standard site is active.",
        )
        to_date: str = pydantic.Field(
            default_factory=lambda: (datetime.date.today() - datetime.timedelta(days=1)).strftime(
                "%Y-%m-%d"
            ),
            pattern=DATE_STRING_PATTERN,
            description="Date in format `YYYY-MM-DD` until which this standard site is active. Default is yesterday.",
        )

        @pydantic.model_validator(mode="after")
        def check_date_order(self) -> GGGProfilesDownloaderSubConfigs.GGG2020StandardSitesItem:
            if self.from_date_parsed > self.to_date_parsed:
                raise ValueError("from_date must be before to_date")
            return self

        @property
        def from_date_parsed(self) -> datetime.date:
            return parse_date_string(self.from_date)

        @property
        def to_date_parsed(self) -> datetime.date:
            return parse_date_string(self.to_date)


class GGGProfilesDownloaderConfig(pydantic.BaseModel):
    """Settings for downloading vertical profiles from the ccycle FTP server."""

    model_config = pydantic.ConfigDict(extra="forbid")

    server: GGGProfilesDownloaderSubConfigs.Server
    scope: Optional[GGGProfilesDownloaderSubConfigs.Scope] = pydantic.Field(
        default=None,
        description="Scope of the vertical profiles to request from the ccycle ftp server. If set to `null`, the script will not request any vertical profiles besides the configured standard sites.",
    )
    ggg2020_standard_sites: list[GGGProfilesDownloaderSubConfigs.GGG2020StandardSitesItem] = (
        pydantic.Field(
            ...,
            validation_alias=pydantic.AliasChoices(
                "ggg2020_standard_sites", "GGG2020_standard_sites"
            ),
            description="List of standard sites to request from the ccycle ftp server. The requests for these standard sites are done before any other requests so that data available for these is not rerequested for other sensors. See https://tccon-wiki.caltech.edu/Main/ObtainingGinputData#Requesting_to_be_added_as_a_standard_site for more information.",
        )
    )


class RetrievalSubConfigs:
    class General(pydantic.BaseModel):
        """Settings applied to all retrieval jobs."""

        model_config = pydantic.ConfigDict(extra="forbid")

        max_process_count: int = pydantic.Field(
            1,
            ge=1,
            le=1024,
            description="How many parallel processes to dispatch. There will be one process per sensor-day. With hyper-threaded CPUs, this can be higher than the number of physical cores.",
        )
        queue_verbosity: Literal["compact", "verbose"] = pydantic.Field(
            "compact",
            description="How much information the retrieval queue should print out. In `verbose` mode it will print out the full list of sensor-days for each step of the filtering process. This can help when figuring out why a certain sensor-day is not processed.",
        )
        container_dir: Optional[str] = pydantic.Field(
            None,
            description="Directory to store the containers in. If not set, it will use `./data/containers` inside the pipeline directory. If your system has enough memory, you could also use `/dev/shm` which is a memory-based file system where files are stored in memory and never written to disk.",
        )

    class JobCustomILS(pydantic.BaseModel):
        model_config = pydantic.ConfigDict(extra="forbid")

        channel1_me: float = pydantic.Field(...)
        channel1_pe: float = pydantic.Field(...)
        channel2_me: float = pydantic.Field(...)
        channel2_pe: float = pydantic.Field(...)

    class Job(pydantic.BaseModel):
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
        from_date: str = pydantic.Field(
            ...,
            pattern=DATE_STRING_PATTERN,
            description="Date string in format `YYYY-MM-DD` from which to consider data in the storage directory.",
        )
        to_date: str = pydantic.Field(
            default_factory=lambda: (datetime.date.today() - datetime.timedelta(days=1)).strftime(
                "%Y-%m-%d"
            ),
            pattern=DATE_STRING_PATTERN,
            description="Date string in format `YYYY-MM-DD` until which to consider data in the storage directory. Default is yesterday.",
        )

        # more advanced settings
        store_binary_spectra: bool = pydantic.Field(
            default=False,
            description="Whether to store the binary spectra files. These are the files that are used by the retrieval algorithm. They are not needed for the output files, but can be useful for debugging.",
        )
        dc_min_threshold: float = pydantic.Field(
            default=0.05,
            ge=0.001,
            le=0.999,
            description="Value used for the `DC_min` threshold in Proffast. If not set, defaults to the Proffast default.",
        )
        dc_var_threshold: float = pydantic.Field(
            default=0.10,
            ge=0.001,
            le=0.999,
            description="Value used for the `DC_var` threshold in Proffast. If not set, defaults to the Proffast default.",
        )
        use_local_pressure_in_pcxs: bool = pydantic.Field(
            default=False,
            description="Whether to use the local pressure in the pcxs files. If not used, it will tell PCXS to use the pressure from the atmospheric profiles (set the input value in the `.inp` file to `9999.9`). If used, the pipeline computes the solar noon time using `skyfield` and averages the local pressure over the time period noon-2h to noon+2h.",
        )
        use_ifg_corruption_filter: bool = pydantic.Field(
            default=True,
            description="Whether to use the ifg corruption filter. This filter is a program based on `preprocess4` and is part of the `tum-esm-utils` library: https://tum-esm-utils.netlify.app/api-reference#tum_esm_utilsinterferograms. If activated, we will only pass the interferograms to the retrieval algorithm that pass the filter - i.e. that won't cause it to crash.",
        )
        custom_ils: dict[str, RetrievalSubConfigs.JobCustomILS] = pydantic.Field(
            default={},
            description="Maps sensor IDs to ILS correction values. If not set, the pipeline will use the values published inside the Proffast Pylot codebase (https://github.com/coccon/proffastpylot).",
            examples=[
                {
                    "ma": {
                        "channel1_me": 0.9892,
                        "channel1_pe": -0.001082,
                        "channel2_me": 0.9892,
                        "channel2_pe": -0.001082,
                    },
                    "mb": {
                        "channel1_me": 0.9893,
                        "channel1_pe": -0.001083,
                        "channel2_me": 0.9893,
                        "channel2_pe": -0.001083,
                    },
                }
            ],
        )
        output_suffix: Optional[str] = pydantic.Field(
            default=None,
            description="Suffix to append to the output folders. If not set, the pipeline output folders are named `sensorid/YYYYMMDD/`. If set, the folders are named `sensorid/YYYYMMDD_suffix/`. This is useful when having multiple retrieval jobs processing the same sensor dates with different settings.",
        )
        pressure_calibration_factors: dict[str, float] = pydantic.Field(
            default={},
            description="Maps sensor IDS to pressure calibration factors. If not set, it is set to 1 for each sensor. `corrected_pressure = input_pressure * calibration_factor + calibration_offset`",
            examples=['{"ma": 0.99981}', '{"ma": 1.00019, "mb": 0.99981}'],
        )
        pressure_calibration_offsets: dict[str, float] = pydantic.Field(
            default={},
            description="Maps sensor IDS to pressure calibration offsets. If not set, it is set to 0 for each sensor. `corrected_pressure = input_pressure * calibration_factor + calibration_offset`",
            examples=['{"ma": -0.00007}', '{"ma": -0.00007, "mb": 0.00019}'],
        )

        @pydantic.model_validator(mode="after")
        def check_model_integrity(self) -> RetrievalSubConfigs.Job:
            if self.from_date_parsed > self.to_date_parsed:
                raise ValueError("from_date must be before to_date")
            if (
                self.retrieval_algorithm == "proffast-1.0"
                and self.atmospheric_profile_model == "GGG2020"
            ):
                raise ValueError("proffast-1.0 does not support GGG2020 profiles")
            return self

        @property
        def from_date_parsed(self) -> datetime.date:
            return parse_date_string(self.from_date)

        @property
        def to_date_parsed(self) -> datetime.date:
            return parse_date_string(self.to_date)


class RetrievalConfig(pydantic.BaseModel):
    """Settings for automated proffast processing. It contains general settings applied to every retrieval job and a list of retrieval jobs to run."""

    model_config = pydantic.ConfigDict(extra="forbid")

    general: RetrievalSubConfigs.General
    jobs: dict[int, RetrievalSubConfigs.Job] = pydantic.Field(
        ...,
        description="List of retrievals to run. The list will be processed sequentially.",
    )


class BundleExportConfig(pydantic.BaseModel):
    """There will be one file per sensor id and atmospheric profile and retrieval algorithm combination.

    The final name looks like `em27-retrieval-bundle-$SENSOR_ID-$RETRIEVAL_ALGORITHM-$ATMOSPHERIC_PROFILE-$FROM_DATE-$TO_DATE$BUNDLE_SUFFIX.$OUTPUT_FORMAT`, e.g.`em27-retrieval-bundle-ma-GGG2020-proffast-2.4-20150801-20240523-v2.1.csv`. The bundle suffix is optional and can be used to distinguish between different internal datasets."""

    model_config = pydantic.ConfigDict(extra="forbid")

    dst_dir: tum_esm_utils.validators.StrictDirectoryPath = pydantic.Field(
        ...,
        description="Directory to write the bundeled outputs to. You should use absolute paths, but if you need relative paths, then this is relative to the caller of the CLI or the pipeline's entrypoint.",
    )
    output_formats: list[Literal["csv", "parquet"]] = pydantic.Field(
        ...,
        description="List of output formats to write the merged output files in. Allowed values are `csv` and `parquet`.",
        examples=[["csv"], ["parquet"], ["csv", "parquet"]],
    )
    from_datetime: str = pydantic.Field(
        ...,
        pattern=UTC_DATETIME_STRING_PATTERN,
        description="UTC datetime in format `YYYY-MM-DDTHH:MM:SSZ` or `YYYY-MM-DDTHH:MM:SS+0000` from which to bundle data",
    )
    to_datetime: str = pydantic.Field(
        ...,
        pattern=UTC_DATETIME_STRING_PATTERN,
        description="UTC datetime in format `YYYY-MM-DDTHH:MM:SSZ` or `YYYY-MM-DDTHH:MM:SS+0000` to which to bundle data",
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
        default=None,
        description="Suffix to append to the output bundles.",
        min_length=1,
        examples=["v2.1", "v2.2", "oco2-gradient-paper-2021"],
    )
    retrieval_job_output_suffix: Optional[str] = pydantic.Field(
        default=None,
        description="When you ran the retrieval with a custom suffix, you can specify it here to only bundle the outputs of this suffix. Use the same value here as in the field `config.retrieval.jobs[i].settings.output_suffix`.",
    )
    parse_dc_timeseries: bool = pydantic.Field(
        default=False,
        description="Whether to parse the DC timeseries from the results directories. This is an output only available in this Pipeline for Proffast2.4. We adapted the preprocessor to output the DC min/mean/max/variation values for each record of data. If you having issues with a low signal intensity on one or both channels, you can run the retrieval with a very low DC_min threshold and filter the data afterwards instead of having to rerun the retrieval.",
    )
    parse_retrieval_diagnostics: bool = pydantic.Field(
        default=False,
        description="Whether to parse the retrieval diagnostics from the results directories - `niter`, `rms`, and `scl` for each retrieval job.",
    )

    @property
    def from_datetime_parsed(self) -> datetime.datetime:
        return parse_datetime_string(self.from_datetime)

    @property
    def to_datetime_parsed(self) -> datetime.datetime:
        return parse_datetime_string(self.to_datetime)

    @pydantic.model_validator(mode="after")
    def check_datetime_order(self) -> BundleExportConfig:
        if self.from_datetime_parsed > self.to_datetime_parsed:
            raise ValueError("from_datetime must be before to_datetime")
        return self


class GEOMSExportConfig(pydantic.BaseModel):
    """There will be one file per retrieval output directory and the h5 files will be stored in the individual output directories of the results folders. Most code of this exporter originates from the GEOMS export code of the PROFFAST Pylot, but we adapted it to fit the output of this pipeline."""

    sensor_ids: list[str] = pydantic.Field(
        ..., description="The sensor ids for which to generate the GEOMS outputs"
    )
    retrieval_algorithms: list[RetrievalAlgorithm] = pydantic.Field(
        ..., description="The retrieval algorithms for which to generate the GEOMS outputs"
    )
    atmospheric_profile_models: list[AtmosphericProfileModel] = pydantic.Field(
        ..., description="The atmospheric profile models for which to generate the GEOMS outputs"
    )
    from_datetime: str = pydantic.Field(
        ...,
        pattern=UTC_DATETIME_STRING_PATTERN,
        description="UTC datetime in format `YYYY-MM-DDTHH:MM:SSZ` or `YYYY-MM-DDTHH:MM:SS+0000` from which to generate GEOMS data",
    )
    to_datetime: str = pydantic.Field(
        ...,
        pattern=UTC_DATETIME_STRING_PATTERN,
        description="UTC datetime in format `YYYY-MM-DDTHH:MM:SSZ` or `YYYY-MM-DDTHH:MM:SS+0000` to which to generate GEOMS data",
    )
    parse_dc_timeseries: bool = pydantic.Field(
        default=False,
        description="Whether to parse the DC timeseries from the results directories. This is an output only available in this Pipeline for Proffast2.4. We adapted the preprocessor to output the DC min/mean/max/variation values for each record of data. If you having issues with a low signal intensity on one or both channels, you can run the retrieval with a very low DC_min threshold and filter the data afterwards instead of having to rerun the retrieval.",
    )
    dc_min_xco2: float = pydantic.Field(
        default=0.05,
        gt=0,
        lt=10,
        description="Only considered if `parse_dc_timeseries` is set. Minimum DC value to consider for XCO2 records in the GEOMS outputs. It not set, it uses the default value of Proffast (0.05).",
    )
    dc_min_xch4: float = pydantic.Field(
        default=0.05,
        gt=0,
        lt=10,
        description="Only considered if `parse_dc_timeseries` is set. Minimum DC value to consider for XCH4 records in the GEOMS outputs. It not set, it uses the default value of Proffast (0.05).",
    )
    dc_min_xh2o: float = pydantic.Field(
        default=0.05,
        gt=0,
        lt=10,
        description="Only considered if `parse_dc_timeseries` is set. Minimum DC value to consider for XH2O records in the GEOMS outputs. It not set, it uses the default value of Proffast (0.05).",
    )
    dc_min_xco: float = pydantic.Field(
        default=0.05,
        gt=0,
        lt=10,
        description="Only considered if `parse_dc_timeseries` is set. Minimum DC value to consider for XCO records in the GEOMS outputs. It not set, it uses the default value of Proffast (0.05).",
    )
    max_sza: Optional[float] = pydantic.Field(
        default=None,
        description="Maximum solar zenith angle to consider in the GEOMS outputs. If not set, it will consider all solar zenith angles.",
    )
    min_xair: Optional[float] = pydantic.Field(
        default=None,
        description="Minimum XAIR required to consider in the GEOMS outputs. If not set, it will consider all XAIR values.",
    )
    max_xair: Optional[float] = pydantic.Field(
        default=None,
        description="Maximum XAIR required to consider in the GEOMS outputs. If not set, it will consider all XAIR values.",
    )
    conflict_mode: Literal["error", "skip", "replace"] = pydantic.Field(
        default="replace",
        description="What to do if an output file already exist.",
    )
    min_datapoints_per_day: int = pydantic.Field(
        default=11,
        ge=1,
        description="Minimum number of data points per day required to generate a GEOMS file for that day. If not enough data points are available, no GEOMS file will be generated for that day.",
    )

    @property
    def from_datetime_parsed(self) -> datetime.datetime:
        return parse_datetime_string(self.from_datetime)

    @property
    def to_datetime_parsed(self) -> datetime.datetime:
        return parse_datetime_string(self.to_datetime)

    @pydantic.model_validator(mode="after")
    def check_datetime_order(self) -> GEOMSExportConfig:
        if self.from_datetime_parsed > self.to_datetime_parsed:
            raise ValueError("from_datetime must be before to_datetime")
        return self


class Config(pydantic.BaseModel):
    """A pydantic model describing the config file schema."""

    model_config = pydantic.ConfigDict(extra="forbid")

    version: Literal["1.11"] = pydantic.Field(
        ...,
        description="Version of the retrieval pipeline which is compatible with this config file. Retrievals done with any version `1.x` will produce the same output files as retrievals done with version `1.0`. But higher version numbers might use a different config file structure and produce more output files.",
    )
    metadata: MetadataConfig
    data: DataConfig
    ggg_profiles_downloader: Optional[GGGProfilesDownloaderConfig] = None
    retrieval: Optional[RetrievalConfig] = None
    bundle_exports: list[BundleExportConfig] = []
    geoms_exports: list[GEOMSExportConfig] = []

    @staticmethod
    def get_config_dir() -> str:
        """Get config/metadata directory path from environment variable if set.

        If not set, returns default config directory path inside the repository."""

        env_path = os.path.join(tum_esm_utils.files.rel_to_abs_path("../../config"), ".env")
        if os.path.isfile(env_path):
            dotenv.load_dotenv(env_path)
        return os.path.abspath(
            os.getenv("ERP_CONFIG_DIR", tum_esm_utils.files.rel_to_abs_path("../../config"))
        )

    @staticmethod
    def get_config_path() -> str:
        """Get config file path from environment variable if set.

        If not set, returns default config file path inside the repository."""

        return os.path.join(Config.get_config_dir(), "config.toml")

    @staticmethod
    def load(
        path: Optional[str] = None,
        ignore_path_existence: bool = False,
    ) -> Config:
        """Load the config file from `config/config.toml` (or any given path).

        If `check_path_existence` is set, it will check whether the paths
        specified in the config file exist."""

        if path is None:
            path = Config.get_config_path()
        path = os.path.abspath(path)

        toml_path: str = path
        json_path: str = path
        if path.endswith(".json"):
            toml_path = path[:-5] + ".toml"
        elif path.endswith(".toml"):
            json_path = path[:-5] + ".json"

        if (not os.path.isfile(toml_path)) and (not os.path.isfile(json_path)):
            raise FileNotFoundError(
                f"Config file not found at {toml_path} or {json_path}. Please create a TOML config file at {toml_path} or put a JSON config file compatible with pipeline version 1.0 - 1.10 at {json_path}."
            )

        config_object: Config
        if os.path.isfile(toml_path):
            with open(toml_path, "rb") as file:
                toml_data = tomli.load(file)
            config_object = Config.model_validate(
                toml_data,
                context={"ignore-path-existence": ignore_path_existence},
            )
        else:
            old_config_object = OldConfig.load(
                json_path, ignore_path_existence=ignore_path_existence
            )
            config_object = Config(
                version="1.11",
                metadata=MetadataConfig(
                    source="local"
                    if any(
                        [
                            os.path.isfile(p)
                            for p in [
                                os.path.join(os.path.dirname(json_path), "locations.json"),
                                os.path.join(os.path.dirname(json_path), "sensors.json"),
                                os.path.join(os.path.dirname(json_path), "campaigns.json"),
                                os.path.join(os.path.dirname(json_path), "events.json"),
                                os.path.join(os.path.dirname(json_path), "em27_metadata.toml"),
                            ]
                        ]
                    )
                    else "github",
                    github_repository=(
                        old_config_object.general.metadata.github_repository
                        if (old_config_object.general.metadata is not None)
                        else None
                    ),
                    github_access_token=(
                        old_config_object.general.metadata.access_token
                        if (old_config_object.general.metadata is not None)
                        else None
                    ),
                ),
                data=DataConfig(
                    atmospheric_profiles=DataSubConfigs.AtmosphericProfiles.model_validate(
                        {"path": old_config_object.general.data.atmospheric_profiles.root},
                        context={"ignore-path-existence": ignore_path_existence},
                    ),
                    ground_pressure=DataSubConfigs.GroundPressure.model_validate(
                        old_config_object.general.data.ground_pressure.model_dump(mode="json"),
                        context={"ignore-path-existence": ignore_path_existence},
                    ),
                    interferograms=DataSubConfigs.Interferograms.model_validate(
                        {
                            "path": old_config_object.general.data.interferograms.root,
                            "ifg_file_regex": (
                                old_config_object.retrieval.general.ifg_file_regex
                                if (old_config_object.retrieval is not None)
                                else ".*"
                            ),
                        },
                        context={"ignore-path-existence": ignore_path_existence},
                    ),
                    results=DataSubConfigs.Results.model_validate(
                        {"path": old_config_object.general.data.results.root},
                        context={"ignore-path-existence": ignore_path_existence},
                    ),
                ),
                ggg_profiles_downloader=(
                    GGGProfilesDownloaderConfig.model_validate(
                        old_config_object.profiles.model_dump(mode="json"),
                        context={"ignore-path-existence": ignore_path_existence},
                    )
                    if (old_config_object.profiles is not None)
                    else None
                ),
                retrieval=(
                    RetrievalConfig(
                        general=RetrievalSubConfigs.General(
                            max_process_count=old_config_object.retrieval.general.max_process_count,
                            queue_verbosity=old_config_object.retrieval.general.queue_verbosity,
                            container_dir=old_config_object.retrieval.general.container_dir,
                        ),
                        jobs={
                            i: RetrievalSubConfigs.Job.model_validate(
                                {
                                    **job.model_dump(mode="json", exclude={"settings"}),
                                    **job.settings.model_dump(mode="json"),
                                },
                                context={"ignore-path-existence": ignore_path_existence},
                            )
                            for i, job in enumerate(old_config_object.retrieval.jobs)
                        },
                    )
                    if (old_config_object.retrieval is not None)
                    else None
                ),
                bundle_exports=(
                    [
                        BundleExportConfig.model_validate(
                            export.model_dump(mode="json"),
                            context={"ignore-path-existence": ignore_path_existence},
                        )
                        for export in old_config_object.bundles
                    ]
                    if (old_config_object.bundles is not None)
                    else []
                ),
                geoms_exports=(
                    [
                        GEOMSExportConfig.model_validate(
                            old_config_object.geoms.model_dump(mode="json"),
                            context={"ignore-path-existence": ignore_path_existence},
                        )
                    ]
                    if (old_config_object.geoms is not None)
                    else []
                ),
            )
            tmp_toml_path = toml_path.removesuffix(".toml") + ".tmp.toml"
            toml_utils.dump_pretty_toml_file(
                filepath=tmp_toml_path,
                data=config_object.model_dump(mode="json", exclude_none=True),
                template_filepath=tum_esm_utils.files.rel_to_abs_path(
                    "../../config/config.template.toml"
                ),
                inline_all_lists=True,
                omit_empty_tables=True,
                omittable_empty_root_arrays=("bundle_exports", "geoms_exports"),
            )
            os.replace(tmp_toml_path, toml_path)

        return config_object
