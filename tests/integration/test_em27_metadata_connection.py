import pytest
import src


@pytest.mark.order(3)
@pytest.mark.integration
@pytest.mark.metadata
def test_metadata_connection() -> None:
    config = src.types.Config.load(ignore_path_existence=True)
    # TODO: refactor metadata loading
    if config.metadata.source == "local":
        src.em27_metadata.load_from_local_files(config_directory=src.types.Config.get_config_dir())
    else:
        assert config.metadata.github_repository is not None, "This should not happen"
        src.em27_metadata.load_from_github(
            github_repository=config.metadata.github_repository,
            access_token=config.metadata.github_access_token,
        )
