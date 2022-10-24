import os
import re

from pathlib import Path
from datetime import datetime
from typing import Optional, TypedDict, Any

from pydantic import BaseConfig, StrictStr, StrictInt, fields, validator, Extra, create_model_from_typeddict

PROJECT_DIR = Path(os.path.abspath(__file__)).parents[2]
DST_DIR = os.path.join(PROJECT_DIR, "location_data")


class ValidationError(Exception):
    """
    Will be raised in any custom checks on config dicts have failed.
    """


class ConfigDict(TypedDict):
    user: StrictStr
    from_date: StrictStr
    to_date: Optional[StrictStr]
    location_repository: StrictStr
    dst_directory: Optional[StrictStr]
    max_idle_time: Optional[StrictInt]


def validate_config_dict(o: Any, skip_filepaths: bool = True) -> None:
    """
    Check, whether a given object is a correct ConfigDict
    Raises a ValidationError if the object is invalid.
    This should always be used when loading the object from a
    JSON file!
    """

    class Config(BaseConfig):
        extra = Extra.forbid
        skip_filepaths: bool

    Config.skip_filepaths = skip_filepaths

    def check_user(cls, v: str) -> str:
        return v

    def check_dates(cls, v: str, field: fields.ModelField, **kwargs) -> str:
        today = datetime.utcnow().strftime("%Y%m%d")
        if v is None:
            v = today
        else:
            try:
                datetime.strptime(v, "%Y%m%d")
            except ValueError as e:
                raise ValueError(f"{field.name} invalid format") from e
            assert v <= today, f"{field.name} is in the future"
        if field.name == "to_date" and "from_date" in kwargs["values"]:
            assert kwargs["values"]["from_date"] <= v, f"from_date after to_date"
        return v

    def check_valid_location_repository(cls, v: str) -> str:
        assert re.match(
            "r^(https://.*)|(git@.*)$", v
        ), f"{v} cannot be a valid location_repository"
        return v

    def check_dst_directory(cls, v: str, config: Config) -> str:
        if v is None:
            v = DST_DIR
        assert config.skip_filepaths or os.path.isdir(v), f"{v} not found"
        return v

    def check_max_idle_time(cls, v: int) -> int:
        assert v >= 0, f"max_idle_time cannot be smaller than zero"
        return v

    validators = {
        "check_user": validator("user")(check_user),
        "check_dates": validator("from_date", "to_date")(check_dates),
        "check_valid_location_repository": validator("location_repository")(
            check_valid_location_repository
        ),
        "check_dst_directory": validator("dst_directory")(check_dst_directory),
        "check_max_idle_time": validator("max_idle_time")(check_max_idle_time),
    }

    create_model_from_typeddict(
        ConfigDict, __config__=Config, __validators__=validators
    ).parse_obj(o)
