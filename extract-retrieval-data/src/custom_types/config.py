from pydantic import BaseModel, validator
from .validators import validate_strict_str, validate_date_string, validate_dir_path


class RequestConfig(BaseModel):
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


class DatabaseConfig(BaseModel):
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


class Config(BaseModel):
    database: DatabaseConfig
    request: RequestConfig
