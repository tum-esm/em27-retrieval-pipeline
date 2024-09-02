import os

import tum_esm_utils


def config_dir_key() -> str:
    return "ERP_CONFIG_DIR"


def get_config_path(
        config_dir_env_var: str
    ) -> str:
    default_config_dir = tum_esm_utils.files.rel_to_abs_path("../../config")
    return os.path.join(
        os.getenv(config_dir_env_var, default_config_dir),
        "config.json"
    )


def get_config_dir(
        config_dir_env_var: str
    ) -> str:
    default_config_dir = tum_esm_utils.files.rel_to_abs_path("../../config")
    return os.getenv(config_dir_env_var, default_config_dir)
