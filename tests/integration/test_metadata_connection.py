import os
import pytest
import em27_metadata
import src


@pytest.mark.order(3)
@pytest.mark.integration
@pytest.mark.metadata
def test_metadata_connection() -> None:
    config = src.types.Config.load(ignore_path_existence=True)
    if config.general.metadata is None:
        em27_metadata.load_from_local_files(
            locations_path=os.path.join(src.types.Config.get_config_dir(), "locations.json"),
            sensors_path=os.path.join(src.types.Config.get_config_dir(), "sensors.json"),
            campaigns_path=os.path.join(src.types.Config.get_config_dir(), "campaigns.json"),
        )
    else:
        em27_metadata.load_from_github(
            github_repository=config.general.metadata.github_repository,
            access_token=config.general.metadata.access_token,
        )
