import os
import pytest
from src import utils


@pytest.mark.integration
def test_load_config() -> None:
    utils.load_config()
