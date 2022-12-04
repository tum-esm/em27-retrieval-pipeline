from pydantic import BaseModel, validator
from .validators import validate_strict_str


class DatabaseConfig(BaseModel):
    host: str
    port: str
    username: str
    password: str
    database_name: str
    table_name: str

    _type_validator_str = validator("*", pre=True)(validate_strict_str)


class Config(BaseModel):
    database: DatabaseConfig
