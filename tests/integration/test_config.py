import pytest

import src
from src import utils

@pytest.mark.order(2)
@pytest.mark.integration
def test_config() -> None:
    config_path = utils.environment.get_config_path()
    src.types.Config.load(config_path)
