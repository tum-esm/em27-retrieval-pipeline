from typing import Optional
from pydantic import BaseModel, validator
from .validators import validate_str, validate_list, validate_bool, validate_int


class DataFilterConfig(BaseModel):
    sensor_ids_to_consider: list[str]
    start_date: str
    end_date: str
    min_days_delay: int

    # validators
    _val_sensor_ids_to_consider = validator(
        "sensor_ids_to_consider", pre=True, allow_reuse=True
    )(
        validate_list(min_len=1),
    )
    _val_date_string = validator(
        *["start_date", "end_date"],
        pre=True,
        allow_reuse=True,
    )(
        validate_str(is_date_string=True),
    )
    _val_min_days_delay = validator("min_days_delay", pre=True, allow_reuse=True)(
        validate_int(minimum=0, maximum=60),
    )


class LocationDataConfig(BaseModel):
    github_repository: str
    access_token: Optional[str]

    # validators
    _val_github_repository = validator("github_repository", pre=True, allow_reuse=True)(
        validate_str(regex=r"^[a-z0-9-_]+/[a-z0-9-_]+$"),
    )
    _val_access_token = validator("access_token", pre=True, allow_reuse=True)(
        validate_str(nullable=True),
    )


class DataSrcDirsConfig(BaseModel):
    datalogger: str
    vertical_profiles: str
    interferograms: str

    # validators
    _val_dir = validator(
        *["datalogger", "vertical_profiles", "interferograms"],
        pre=True,
        allow_reuse=True,
    )(
        validate_str(is_directory=True),
    )


class DataDstDirsConfig(BaseModel):
    results: str

    # validators
    _val_results = validator("results", pre=True, allow_reuse=True)(
        validate_str(is_directory=True)
    )


class Config(BaseModel):
    process_data_automatically: bool
    data_filter: DataFilterConfig
    location_data: LocationDataConfig
    data_src_dirs: DataSrcDirsConfig
    data_dst_dirs: DataDstDirsConfig

    # validators
    _val_dir = validator("process_data_automatically", pre=True, allow_reuse=True)(
        validate_bool()
    )
