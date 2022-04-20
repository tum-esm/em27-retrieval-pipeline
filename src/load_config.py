import json
import os
from cerberus import Validator

dir = os.path.dirname
PROJECT_DIR = dir(dir(os.path.abspath(__file__)))

validator = Validator(
    {
        "lat": {"type": "float"},
        "lng": {"type": "float"},
        "dates": {"type": "list", "schema": {"type": "string"}},
        "user": {"type": "string"},
        "dst": {"type": "string"},
        "downloadTypes": {
            "type": "dict",
            "schema": {"map": {"type": "boolean"}, "mod": {"type": "boolean"}},
        },
        "downloadMod": {"type": "boolean"},
        "minimumDaysDelay": {"type": "integer", "min": 0},
        "downloadTimeoutSeconds": {"type": "integer", "min": 0},
    }
)


def run():
    try:
        with open(f"{PROJECT_DIR}/config.json", "r") as f:
            CONFIG = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError("config.json does not exist")
    except json.decoder.JSONDecodeError:
        raise AssertionError("config.json is not in a valid JSON format")

    assert validator.validate(CONFIG), f"Invalid config.json: {validator.errors}"

    return CONFIG
