import shutil
from tests.test_pylot import _assert_output_file_integrity, _generate_pylot_config, _generate_pylot_log_format, _set_up_empty_output_directory
import pytest
from src.pylot_factory import PylotFactory
from tests.fixtures import wrap_test_with_mainlock
import glob
import os
import sys


@pytest.mark.integration
def test_pylot_factory(wrap_test_with_mainlock):
    _set_up_empty_output_directory()
    pylot_config_path = _generate_pylot_config()
    _generate_pylot_log_format()

    factory = PylotFactory()
    assert os.path.exists(factory.main)

    container_id = factory.create_pylot_instance()
    
    factory.execute_pylot(container_id, pylot_config_path, 1)
    _assert_output_file_integrity()
