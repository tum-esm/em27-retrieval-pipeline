import json
import os
from cerberus import Validator

dir = os.path.dirname
PROJECT_DIR = dir(dir(os.path.abspath(__file__)))

validator = Validator(
    {
        "stationId": {"type": "string"},
        "lat": {"type": "float"},
        "lng": {"type": "float"},
        "dates": {"type": "list", "schema": {"type": "string"}},
        "user": {"type": "string"},
        "dst": {"type": "string"},
        "downloadTypes": {
            "type": "dict",
            "schema": {
                "map": {"type": "boolean"},
                "mod": {"type": "boolean"}
            },
        },
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
