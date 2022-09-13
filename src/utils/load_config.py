import json
import os
from src import types

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))


def load_config(validate: bool = False, skip_filepaths: bool = False) -> dict:
    try:
        with open(os.path.join(PROJECT_DIR, "config", "config.json"), "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError("config.json does not exist")
    except json.decoder.JSONDecodeError:
        raise AssertionError("config.json is not in a valid JSON format")

    if validate:
        types.validate_config_dict(config, skip_filepaths=skip_filepaths)

    return config
