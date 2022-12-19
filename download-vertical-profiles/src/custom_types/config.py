import os
from pathlib import Path

from datetime import datetime
from pydantic import BaseModel, validator
from .validators import validate_str, validate_int

from src.custom_types import Version
from src.custom_types.location_data_types import dt_to_str

PROJECT_PATH = Path(os.path.abspath(__file__)).parents[2]


class RequestConfig(BaseModel):

    versions: list[Version] = ["GGG2014"]
    from_date: str = "00010101"
    to_date: str = dt_to_str(datetime.utcnow())
    dst_dir: str = os.path.join(PROJECT_PATH, "vertical-profiles")

    _val_dates = validator("from_date", "to_date", pre=True, allow_reuse=True,)(
        validate_str(is_date=True),
    )

    _val_dst_dir = validator("dst_dir", pre=True, allow_reuse=True,)(
        validate_str(is_dir=True),
    )


class FTPConfig(BaseModel):
    email: str
    max_day_delay: int = 7
    upload_sleep: int = 60
    upload_timeout: int = 180
    download_sleep: int = 60
    download_timeout: int = 600

    _val_dates = validator("email", pre=True, allow_reuse=True,)(
        validate_str(regex=r"[^@]+@[^@]+\.[^@]+"),
    )

    _val_max_delay = validator("max_day_delay", pre=True, allow_reuse=True,)(
        validate_int(minimum=0, maximum=10),
    )

    _val_max_await = validator(
        "upload_sleep",
        "upload_timeout",
        "download_sleep",
        "download_timeout",
        pre=True,
        allow_reuse=True,
    )(
        validate_int(minimum=0),
    )


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
    ftp: FTPConfig
    request: RequestConfig

    class Config:
        extra = "forbid"
