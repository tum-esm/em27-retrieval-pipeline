import os
from typing import get_args
from pathlib import Path

from datetime import datetime
from pydantic import BaseModel, validator
from .validators import validate_str, validate_bool

from src.custom_types import Rate, DataType

PROJECT_PATH = Path(os.path.abspath(__file__)).parents[2]


class RequestConfig(BaseModel):

    campaign_name: str
    from_date: str = "00010101"
    to_date: str = datetime.strftime(datetime.utcnow(), "%Y%m%d")
    proffast_version: str = "2.2"
    data_types: list[DataType] = list(get_args(DataType))
    sampling_rate: Rate = "1 min"
    override_data: bool = False
    dst_dir: str = os.path.join(PROJECT_PATH, "retrieval-data")

    _val_str = validator(
        "proffast_version",
        "campaign_name",
        "sampling_rate",
        "data_types",
        pre=True,
        allow_reuse=True,
    )(
        validate_str(),
    )

    _val_dates = validator("from_date", "to_date", pre=True, allow_reuse=True,)(
        validate_str(is_date=True),
    )

    _val_override_data = validator("override_data", pre=True, allow_reuse=True,)(
        validate_bool(),
    )

    _val_dst_dir = validator("dst_dir", pre=True, allow_reuse=True,)(
        validate_str(is_dir=True),
    )

    class Config:
        extra = "forbid"


class DatabaseConfig(BaseModel):
    host: str
    username: str
    password: str
    database_name: str
    port: str = "5432"
    table_name: str = "measurements"

    _val_str = validator("*", pre=True, allow_reuse=True,)(
        validate_str(),
    )

    class Config:
        extra = "forbid"


class GitHubConfig(BaseModel):
    username: str
    token: str
    data_dir: str

    _val_str = validator("username", "token", pre=True, allow_reuse=True,)(
        validate_str(),
    )

    _val_data_dir = validator("data_dir", pre=True, allow_reuse=True,)(
        validate_str(regex=r"(https://raw.githubusercontent.com/.*)"),
    )

    class Config:
        extra = "forbid"


class Config(BaseModel):
    github: GitHubConfig
    database: DatabaseConfig
    request: RequestConfig

    class Config:
        extra = "forbid"
