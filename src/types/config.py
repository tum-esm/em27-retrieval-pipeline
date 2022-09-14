from datetime import datetime
import os
import pydantic
from typing import Any, TypedDict
from .validation_error import ValidationError


class _ConfigDictSrcIfgs(TypedDict):
    upload: str
    other: list[str]


class _ConfigDictSrc(TypedDict):
    datalogger: str
    vertical_profiles: str
    interferograms: _ConfigDictSrcIfgs


class ConfigDict(TypedDict):
    sensors_to_consider: list[str]
    process_uploads_automatically: bool
    src: _ConfigDictSrc
    location_repository: str
    dst: str
    start_date: str


class _ValidationModel(pydantic.BaseModel):
    o: ConfigDict

    class Config:
        extra = "forbid"


def validate_config_dict(o: Any, skip_filepaths: bool = False) -> None:
    """
    Check, whether a given object is a correct ConfigDict
    Raises a pydantic.ValidationError if the object is invalid.

    This should always be used when loading the object from a
    JSON file!
    """
    try:
        _ValidationModel(o=o)
    except pydantic.ValidationError as e:
        pretty_error_messages = []
        for error in e.errors():
            fields = [str(f) for f in error["loc"][1:] if f not in ["__root__"]]
            pretty_error_messages.append(f"{'.'.join(fields)} -> {error['msg']}")
        raise ValidationError(f"config is invalid: {', '.join(pretty_error_messages)}")

    new_config: ConfigDict = o

    try:
        if not skip_filepaths:
            assert os.path.isdir(
                new_config["dst"]
            ), f'directory "{new_config["dst"]}" does not exist'

            data_src_dirs = [
                new_config["src"]["datalogger"],
                new_config["src"]["vertical_profiles"],
                new_config["src"]["interferograms"]["upload"],
                *new_config["src"]["interferograms"]["other"],
            ]

            for data_src_dir in data_src_dirs:
                assert os.path.isdir(
                    data_src_dir
                ), f'directory "{data_src_dir}" does not exist'
                for sensor in new_config["sensors_to_consider"]:
                    sensor_dir = os.path.join(data_src_dir, sensor)
                    assert os.path.isdir(
                        sensor_dir
                    ), f'directory "{sensor_dir}" does not exist'

        try:
            datetime.strptime(new_config["start_date"], "%Y%m%d")
        except:
            raise AssertionError(f"config.start_date is not a valid date")

    except AssertionError as e:
        raise ValidationError(f"config is invalid: {e}")
