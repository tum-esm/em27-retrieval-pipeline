from pydantic import BaseModel, validator
from .validators import validate_str, validate_list, validate_bool


class DataFilterConfig(BaseModel):
    sensors_to_consider: list[str]
    start_date: str
    end_date: str

    # validators
    _val_sensors_to_consider = validator(
        "sensors_to_consider", pre=True, allow_reuse=True
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


class DataSrcConfig(BaseModel):
    location_repository: str
    datalogger_dir: str
    vertical_profiles_dir: str
    interferograms_dir: str

    # validators
    _val_location_repository = validator(
        "location_repository", pre=True, allow_reuse=True
    )(
        validate_str(regex=r"^git@.+:.+/.+$"),
    )
    _val_dir = validator(
        *["datalogger_dir", "vertical_profiles_dir", "interferograms_dir"],
        pre=True,
        allow_reuse=True,
    )(
        validate_str(is_directory=True),
    )


class DataDstConfig(BaseModel):
    results_dir: str

    # validators
    _val_dir = validator("results_dir", pre=True, allow_reuse=True)(
        validate_str(is_directory=True)
    )


class ConfigDict(BaseModel):
    process_data_automatically: bool
    data_filter: DataFilterConfig
    data_src: DataSrcConfig
    data_dst: DataDstConfig

    # validators
    _val_dir = validator("process_data_automatically", pre=True, allow_reuse=True)(
        validate_bool()
    )
