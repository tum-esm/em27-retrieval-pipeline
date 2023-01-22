import json
import os
from src import custom_types

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))


def load_config() -> custom_types.Config:
    try:
        with open(os.path.join(PROJECT_DIR, "config", "config.json"), "r") as f:
            config_file_content = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError("config.json does not exist")
    except json.decoder.JSONDecodeError:
        raise AssertionError("config.json is not in a valid JSON format")

    try:
        return custom_types.Config(**config_file_content)
    except Exception as e:
        raise ValueError(f"config.json not in a valid format: {e}")
