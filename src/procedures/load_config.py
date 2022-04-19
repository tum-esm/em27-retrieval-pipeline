import json
import os
from cerberus import Validator

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))

validator = Validator(
    {
        "download_map_data_email": {"type": "string"},
        "sensors_to_consider": {"type": "list", "schema": {"type": "string"}},
        "sensor_coordinates": {
            "type": "dict",
            "keysrules": {"type": "string", "regex": "[a-z]+"},
            "valuesrules": {
                "type": "dict",
                "schema": {
                    "lat": {"type": "number"},
                    "lng": {"type": "number"},
                    "alt": {"type": "number"},
                },
            },
        },
        "sensor_serial_numbers": {
            "type": "dict",
            "keysrules": {"type": "string", "regex": "[a-z]+"},
            "valuesrules": {"type": "number"},
        },
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
    for sensor in CONFIG["sensors_to_consider"]:
        assert (
            sensor in CONFIG["sensor_coordinates"].keys()
        ), f'Invalid config.json: sensor {sensor} not in "sensor_coordinates"'
        assert (
            sensor in CONFIG["sensor_serial_numbers"].keys()
        ), f'Invalid config.json: sensor {sensor} not in "sensor_serial_numbers"'

    return CONFIG
