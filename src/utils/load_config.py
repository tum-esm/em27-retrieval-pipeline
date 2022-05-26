import json
import os
from cerberus import Validator

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))

validator = Validator(
    {
        "download_map_data_email": {"type": "string"},
        "sensors_to_consider": {"type": "list", "schema": {"type": "string"}},
    }
)


def load_config():
    try:
        with open(f"{PROJECT_DIR}/config.json", "r") as f:
            CONFIG = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError("config.json does not exist")
    except json.decoder.JSONDecodeError:
        raise AssertionError("config.json is not in a valid JSON format")

    assert validator.validate(CONFIG), f"Invalid config.json: {validator.errors}"

    return CONFIG
