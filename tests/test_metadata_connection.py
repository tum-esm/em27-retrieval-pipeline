import pytest
import tum_esm_em27_metadata
from src import utils


@pytest.mark.integration
def test_metadata_connection() -> None:
    config = utils.config.Config.load()
    tum_esm_em27_metadata.load_from_github(
        github_repository=config.general.location_data.github_repository,
        access_token=config.general.location_data.access_token,
    )
