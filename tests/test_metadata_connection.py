import pytest
import tum_esm_em27_metadata
from src import custom_types


@pytest.mark.integration
def test_metadata_connection() -> None:
    config = custom_types.Config.load()
    tum_esm_em27_metadata.load_from_github(
        github_repository=config.general.location_data.github_repository,
        access_token=config.general.location_data.access_token,
    )
