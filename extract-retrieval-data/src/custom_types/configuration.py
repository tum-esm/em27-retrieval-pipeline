from pydantic import BaseModel, validator
from .validators import (
    validate_strict_str,
    validate_date_string,
    validate_dir_path,
    validate_raw_repository,
)


class RequestConfiguration(BaseModel):
    campaign_name: str
    from_date: str
    to_date: str
    dst_dir: str

    _type_validator_string = validator(
        "*",
        pre=True,
        allow_reuse=True,
    )(validate_strict_str)
    _type_validator_date_string = validator(
        "from_date",
        "to_date",
        pre=True,
        allow_reuse=True,
    )(validate_date_string)
    _type_validator_dir_path = validator(
        "dst_dir",
        pre=True,
        allow_reuse=True,
    )(validate_dir_path)


class DatabaseConfiguration(BaseModel):
    host: str
    port: str
    username: str
    password: str
    database_name: str
    table_name: str

    _type_validator_string = validator(
        "*",
        pre=True,
        allow_reuse=True,
    )(validate_strict_str)


class LocationDataConfiguration(BaseModel):
    git_username: str
    git_token: str
    git_data_dir: str

    _type_validator_string = validator(
        "*",
        pre=True,
        allow_reuse=True,
    )(validate_strict_str)
    _type_validator_string = validator(
        "git_data_dir",
        pre=True,
        allow_reuse=True,
    )(validate_raw_repository)


class Configuration(BaseModel):
    location_data: LocationDataConfiguration
    database: DatabaseConfiguration
    request: RequestConfiguration
