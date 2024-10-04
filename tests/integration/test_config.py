import pytest
import os
import tum_esm_utils
from src.utils.files import read_yaml
import src

@pytest.mark.order(2)
@pytest.mark.integration
def test_config() -> None:
    config_setup = read_yaml(tum_esm_utils.files.rel_to_abs_path("../../config_setup.yml"))
    if config_setup['alternate_config_dir'] is None:
        config_path = None # default config path
    else:
        config_path = os.path.join(config_setup["alternate_config_dir"], "config.json")
    src.types.Config.load(config_path)
