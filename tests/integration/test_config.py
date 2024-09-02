import pytest

import src
from src.utils.envutils import get_config_path, config_dir_key

@pytest.mark.order(2)
@pytest.mark.integration
def test_config() -> None:
    config_path = get_config_path(config_dir_key())
    src.types.Config.load(config_path)
