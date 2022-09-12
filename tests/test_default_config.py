import pytest
from src import utils
from tests.fixtures import provide_tmp_config


@pytest.mark.ci
def test_default_config(provide_tmp_config):
    utils.load_config(validate=True, skip_directory_paths=True)
