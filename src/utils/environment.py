import os

import tum_esm_utils


CONFIG_DIR_KEY = "ERP_CONFIG_DIR"


def get_config_dir() -> str:
    default_config_dir = tum_esm_utils.files.rel_to_abs_path("../../config")
    return os.getenv(CONFIG_DIR_KEY, default_config_dir)


def get_config_path() -> str:
    default_config_dir = get_config_dir()
    return os.path.join(
        os.getenv(CONFIG_DIR_KEY, default_config_dir),
        "config.json"
    )
