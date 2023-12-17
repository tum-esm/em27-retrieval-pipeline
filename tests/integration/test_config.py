import pytest
from src import types


@pytest.mark.integration
def test_config() -> None:
    types.Config.load()
