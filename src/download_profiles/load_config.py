import json
import os
from cerberus import Validator

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))

validator = Validator(
    {
        "stationId": {"type": "string"},
        "lat": {"type": "float"},
        "lon": {"type": "float"},
        "dates": {"type": "list", "schema": {"type": "string"}},
        "user": {"type": "string"},
        "dst": {"type": "string"},
        "sharedCachePath": {"type": "string", 'nullable': True},
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

    if config["sharedCachePath"] == None:
        config["sharedCachePath"] = PROJECT_DIR + "/cache"
    elif config["sharedCachePath"].endswith("/"):
        config["sharedCachePath"] = config["sharedCachePath"][:-1]
    
    assert os.path.isdir(config["sharedCachePath"]), "sharedCachePath directory does not exist"
    return config
