import pytest
from src import utils


@pytest.mark.integration
def test_local_config():
    utils.load_config(validate=True)
