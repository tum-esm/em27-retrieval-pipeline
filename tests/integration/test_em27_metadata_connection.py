import pytest
import src


@pytest.mark.order(3)
@pytest.mark.integration
@pytest.mark.metadata
def test_metadata_connection() -> None:
    config = src.types.Config.load(ignore_path_existence=True)
    src.em27_metadata.load_from_config(
        source=config.metadata.source,
        github_repository=config.metadata.github_repository,
        github_access_token=config.metadata.github_access_token,
        config_directory=src.types.Config.get_config_dir(),
    )
