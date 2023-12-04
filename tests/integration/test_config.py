import pytest
import src


@pytest.mark.integration
def test_config() -> None:
    src.utils.config.Config.load()
