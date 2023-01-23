import pytest
from src import utils


@pytest.mark.integration
def test_local_config() -> None:
    utils.load_config()
