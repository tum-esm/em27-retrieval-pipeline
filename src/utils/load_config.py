import json
import os
import tum_esm_utils
from src import custom_types

_PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=4)
_CONFIG_PATH = os.path.join(_PROJECT_DIR, "config", "config.json")


def load_config() -> custom_types.Config:
    try:
        config_file_content = tum_esm_utils.files.load_json_file(_CONFIG_PATH)
    except FileNotFoundError:
        raise FileNotFoundError("config.json does not exist")
    except json.decoder.JSONDecodeError:
        raise ValueError("config.json is not in a valid JSON format")

    try:
        return custom_types.Config(**config_file_content)
    except Exception as e:
        raise ValueError(f"config.json not in a valid format: {e}")
