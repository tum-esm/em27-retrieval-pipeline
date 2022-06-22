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
                "datalogger": {"type": "string", "check_with": check_directory_path},
                "verticalProfiles": {
                    "type": "string",
                    "check_with": check_directory_path,
                },
                "interferograms": {
                    "type": "dict",
                    "require_all": True,
                    "schema": {
                        "upload": {
                            "type": "dict",
                            "require_all": True,
                            "keysrules": {"type": "string"},
                            "valuesrules": {
                                "type": "string",
                                "check_with": check_directory_path,
                            },
                        },
                        "other": {
                            "type": "dict",
                            "require_all": True,
                            "valuesrules": {
                                "type": "list",
                                "schema": {
                                    "type": "string",
                                    "check_with": check_directory_path,
                                },
                            },
                        },
                    },
                },
            },
        },
        "locationRepository": {"type": "string", "regex": "^https://.*$"},
        "dst": {"type": "string", "check_with": check_directory_path},
        "startDate": {"type": "integer", "check_with": check_date_int},
        "proffastVersion": {"type": "string", "allowed": ["2.0.1", "2.1.1"]},
    }
)


def load_config(validate=False) -> tuple[str, dict]:
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

            ifg_upload_keys = CONFIG["src"]["interferograms"]["upload"].keys()
            ifg_other_keys = CONFIG["src"]["interferograms"]["other"].keys()
            for s in CONFIG["sensorsToConsider"]:
                assert (
                    s in ifg_upload_keys
                ), f'sensor "{s}" does not have an ifg-upload directory'
                assert (
                    s in ifg_other_keys
                ), f'sensor "{s}" does not have a list with other ifg-directories'

        except AssertionError as e:
            raise AssertionError(f"Invalid config.json: {e}")

    return CONFIG
