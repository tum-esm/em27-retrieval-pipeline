import json
import os
import tum_esm_utils
from src import custom_types

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))


def load_config() -> custom_types.Config:
    try:
        config_file_content = tum_esm_utils.files.load_json_file(
            os.path.join(PROJECT_DIR, "config", "config.json")
        )
    except FileNotFoundError:
        raise FileNotFoundError("config.json does not exist")
    except json.decoder.JSONDecodeError:
        raise ValueError("config.json is not in a valid JSON format")

    try:
        return custom_types.Config(**config_file_content)
    except Exception as e:
        raise ValueError(f"config.json not in a valid format: {e}")
