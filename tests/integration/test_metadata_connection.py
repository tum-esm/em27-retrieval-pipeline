import pytest
import em27_metadata
import src


@pytest.mark.order(3)
@pytest.mark.integration
def test_metadata_connection() -> None:
    config = src.types.Config.load()
    if config.general.metadata is None:
        pytest.skip("Remote metadata not configured")
    else:
        em27_metadata.load_from_github(
            github_repository=config.general.metadata.github_repository,
            access_token=config.general.metadata.access_token,
        )
