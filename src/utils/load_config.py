from datetime import datetime
import json
import os
import cerberus

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
CONFIG_FILE = f"{PROJECT_DIR}/config/config.json"


def check_date_int(field, value, error):
    try:
        datetime.strptime(str(value), "%Y%m%d")
    except ValueError:
        error(field, "value has to be a valid date")


def check_directory_path(field, value: str, error):
    try:
        assert os.path.isdir(value), "value has to be a valid directoy"
        assert not value.endswith("/"), 'path should not end with "/"'
    except AssertionError as e:
        error(field, str(e))


validator = cerberus.Validator(
    {
        "sensorsToConsider": {"type": "list", "schema": {"type": "string"}},
        "processUploadsAutomatically": {"type": "boolean"},
        "src": {
            "type": "dict",
            "require_all": True,
            "schema": {
                "datalogger": {"type": "string"},
                "verticalProfiles": {"type": "string"},
                "interferograms": {
                    "type": "dict",
                    "require_all": True,
                    "schema": {
                        "upload": {"type": "string"},
                        "other": {
                            "type": "list",
                            "schema": {"type": "string"},
                        },
                    },
                },
            },
        },
        "locationRepository": {"type": "string", "regex": "^(https://.*)|(git@.*)$"},
        "dst": {"type": "string", "check_with": check_directory_path},
        "startDate": {"type": "integer", "check_with": check_date_int},
    }
)


def load_config(validate=False) -> dict:
    try:
        with open(CONFIG_FILE, "r") as f:
            CONFIG = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError("config.json does not exist")
    except json.decoder.JSONDecodeError:
        raise AssertionError("config.json is not in a valid JSON format")

    if validate:
        try:
            assert validator.validate(CONFIG), validator.errors
            data_src_dirs = [
                CONFIG["src"]["datalogger"],
                CONFIG["src"]["verticalProfiles"],
                CONFIG["src"]["interferograms"]["upload"],
                *CONFIG["src"]["interferograms"]["other"],
            ]

            for data_src_dir in data_src_dirs:
                assert os.path.isdir(data_src_dir), f'"{data_src_dir}" does not exist'
                for sensor in CONFIG["sensorsToConsider"]:
                    sensor_dir = os.path.join(data_src_dir, sensor)
                    assert os.path.isdir(sensor_dir), f'"{sensor_dir}" does not exist'

        except AssertionError as e:
            raise AssertionError(f"Invalid config.json: {e}")

    return CONFIG
