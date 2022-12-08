import os
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel, validator
from .validators import (
    validate_strict_str,
    validate_strict_int,
    validate_strict_bool,
    validate_dir_path,
    validate_raw_repository,
    validate_date_str,
)

from src.custom_types import Rate, DataType

PROJECT_PATH = Path(os.path.abspath(__file__)).parents[3]


class RequestConfig(BaseModel):
    campaign_name: str
    from_date: str = "00010101"
    to_date: str = datetime.strftime(datetime.utcnow(), "%Y%m%d")
    proffast_version: str = "2.2"
    data_types: list[DataType] = [
        "gnd_p",
        "gnd_t",
        "app_sza",
        "xh2o",
        "xair",
        "xco2",
        "xch4",
        "xco",
    ]
    sampling_rate: Rate = "1 min"
    override_data: bool = False
    dst_dir: str = os.path.join(PROJECT_PATH, "retrieval-data")

    _type_validator_string = validator(
        "proffast_version",
        "campaign_name",
        "sampling_rate",
        "from_date",
        "to_date",
        "dst_dir",
        pre=True,
        allow_reuse=True,
    )(validate_strict_str)

    _type_validator_bool = validator(
        "override_data",
        pre=True,
        allow_reuse=True,
    )(validate_strict_bool)

    _type_validator_date_string = validator(
        "from_date",
        "to_date",
        pre=True,
        allow_reuse=True,
    )(validate_date_str)

    _type_validator_dir_path = validator(
        "dst_dir",
        pre=True,
        allow_reuse=True,
    )(validate_dir_path)

    class Config:
        extra = "forbid"


class DatabaseConfig(BaseModel):
    host: str
    port: int = 5432
    username: str
    password: str
    database_name: str
    table_name: str = "measurements"

    _type_validator_string = validator(
        "database_name",
        "table_name",
        "password",
        "username",
        "host",
        pre=True,
        allow_reuse=True,
    )(validate_strict_str)

    _type_validator_string = validator(
        "port",
        pre=True,
        allow_reuse=True,
    )(validate_strict_int)

    class Config:
        extra = "forbid"


class GitConfig(BaseModel):
    username: str
    token: str
    data_dir: str

    _type_validator_string = validator(
        "*",
        pre=True,
        allow_reuse=True,
    )(validate_strict_str)
    _type_validator_string = validator(
        "data_dir",
        pre=True,
        allow_reuse=True,
    )(validate_raw_repository)

    class Config:
        extra = "forbid"


class Config(BaseModel):
    git: GitConfig
    database: DatabaseConfig
    request: RequestConfig

    class Config:
        extra = "forbid"
