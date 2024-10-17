import pytest
import em27_metadata

import src
from src import utils

@pytest.mark.order(3)
@pytest.mark.integration
def test_metadata_connection() -> None:
    config_path = utils.environment.get_config_path()
    config = src.types.Config.load(config_path)
    if config.general.metadata is None:
        pytest.skip("Remote metadata not configured")
    else:
        em27_metadata.load_from_github(
            github_repository=config.general.metadata.github_repository,
            access_token=config.general.metadata.access_token,
        )
