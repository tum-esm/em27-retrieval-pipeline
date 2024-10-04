import pytest
import os
import em27_metadata
import tum_esm_utils
from src.utils.files import read_yaml
import src


@pytest.mark.order(3)
@pytest.mark.integration
def test_metadata_connection() -> None:
    config_setup = read_yaml(tum_esm_utils.files.rel_to_abs_path("../../config_setup.yml"))
    if config_setup['alternate_config_dir'] is None:
        config_path = None # default config path
    else:
        config_path = os.path.join(config_setup["alternate_config_dir"], "config.json")
    config = src.types.Config.load(config_path)
    if config.general.metadata is None:
        pytest.skip("Remote metadata not configured")
    else:
        em27_metadata.load_from_github(
            github_repository=config.general.metadata.github_repository,
            access_token=config.general.metadata.access_token,
        )
