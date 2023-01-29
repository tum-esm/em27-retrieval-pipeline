import os
import shutil
import filelock
import pytest
from src import utils

dir = os.path.dirname
PROJECT_DIR = dir(dir(os.path.abspath(__file__)))
lock = filelock.FileLock(os.path.join(PROJECT_DIR, "src", "main.lock"), timeout=0)


@pytest.fixture
def wrap_test_with_mainlock():
    try:
        lock.acquire()
        yield
        lock.release()
    except filelock.Timeout:
        raise Exception("automation is already running")


@pytest.fixture
def download_sample_data():
    sample_data_path = os.path.join(PROJECT_DIR, "example", "inputs")
    if not os.path.isdir(sample_data_path):
        filename = "automated-proffast-pylot-example-inputs.tar.gz"
        utils.run_shell_command(
            f"wget --quiet https://syncandshare.lrz.de/dl/fiA9bjdafNcuVGrmMfDL49/{filename}",
            working_directory=os.path.join(PROJECT_DIR, "example"),
        )
        utils.run_shell_command(
            f"tar -xf {filename}",
            working_directory=os.path.join(PROJECT_DIR, "example"),
        )
        os.remove(os.path.join(PROJECT_DIR, "example", filename))

    assert os.path.isdir(os.path.join(sample_data_path, "ifg"))
    assert os.path.isdir(os.path.join(sample_data_path, "log"))
    assert os.path.isdir(os.path.join(sample_data_path, "map"))

    yield


@pytest.fixture
def provide_tmp_config():
    config_path = os.path.join(PROJECT_DIR, "config", "config.json")
    tmp_config_path = os.path.join(PROJECT_DIR, "config", "config.tmp.json")
    default_config_path = os.path.join(PROJECT_DIR, "config", "config.template.json")

    assert not os.path.isfile(tmp_config_path), f'"{tmp_config_path}" should not exist'
    assert os.path.isfile(default_config_path), f'"{default_config_path}" should exist'

    local_config_exists = os.path.isfile(config_path)
    if local_config_exists:
        os.rename(config_path, tmp_config_path)

    shutil.copyfile(default_config_path, config_path)
    yield
    os.remove(config_path)

    if local_config_exists:
        os.rename(tmp_config_path, config_path)
