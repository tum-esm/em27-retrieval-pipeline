import json
import os
from cerberus import Validator

from src.utils.time_utils import TimeUtils

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))

validator = Validator(
    {
        "from": {"type": "number", "check_with": TimeUtils.date_string_is_valid},
        "to": {"type": "number", "nullable": True, "check_with": TimeUtils.date_string_is_valid},
        "user": {"type": "string"},
        "dst": {"type": "string"},
        "downloadTimeoutSeconds": {"type": "integer", "min": 0},
    }
)


def run(validate=False):
    try:
        with open(f"{PROJECT_DIR}/config.json", "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError("config.json does not exist")
    except json.decoder.JSONDecodeError:
        raise AssertionError("config.json is not in a valid JSON format")

    if validate:
        assert validator.validate(config), f"Invalid config.json: {validator.errors}"

    return config
