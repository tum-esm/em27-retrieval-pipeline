from datetime import datetime
import json
import os
from cerberus import Validator

def check_date_int(field, value, error):
    if value is not None:
        try:
            datetime.strptime(str(value), "%Y%m%d")
        except ValueError:
            error(field, 'value has to be a valid date')
            
dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))

validator = Validator(
    {
        "from": {"type": "number", "check_with": check_date_int},
        "to": {"type": "number", "nullable": True, "check_with": check_date_int},
        "user": {"type": "string"},
        "dst": {"type": "string"},
        "downloadTimeoutSeconds": {"type": "integer", "min": 0},
        "locationRepository": {"type": "string", "regex": '^https://.*$'},
    }
)


def load_setup(validate=False):
    try:
        with open(f"{PROJECT_DIR}/config.json", "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError("config.json does not exist")
    except json.decoder.JSONDecodeError:
        raise AssertionError("config.json is not in a valid JSON format")

    if validate:
        assert validator.validate(config), f"Invalid config.json: {validator.errors}"

    return PROJECT_DIR, config
