from datetime import datetime
import json
import os
from cerberus import Validator

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))


def check_date_int(field, value, error):
    try:
        datetime.strptime(str(value), "%Y%m%d")
    except ValueError:
        error(field, "value has to be a valid date")


def check_directory_path(field, value, error):
    try:
        assert os.path.isdir(value)
    except AssertionError:
        error(field, "value has to be a valid date")


validator = Validator(
    {
        "sensorsToConsider": {"type": "list", "schema": {"type": "string"}},
        "src": {
            "type": "dict",
            "require_all": True,
            "schema": {
                "datalogger": {"type": "string", "check_with": check_directory_path},
                "verticalProfiles": {
                    "type": "string",
                    "check_with": check_directory_path,
                },
                "interferograms": {
                    "type": "string",
                    "check_with": check_directory_path,
                },
            },
        },
        "locationRepository": {"type": "string", "regex": "^https://.*$"},
        "dst": {"type": "string", "check_with": check_directory_path},
        "startDate": {"type": "integer", "check_with": check_date_int},
    }
)


def load_setup(validate=False) -> tuple[str, dict]:
    try:
        with open(f"{PROJECT_DIR}/config.json", "r") as f:
            CONFIG = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError("config.json does not exist")
    except json.decoder.JSONDecodeError:
        raise AssertionError("config.json is not in a valid JSON format")

    if validate:
        assert validator.validate(CONFIG), f"Invalid config.json: {validator.errors}"

    return PROJECT_DIR, CONFIG
