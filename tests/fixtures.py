import os
import shutil
import filelock
import pytest

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
def provide_tmp_config():
    config_path = os.path.join(PROJECT_DIR, "config", "config.json")
    tmp_config_path = os.path.join(PROJECT_DIR, "config", "config.tmp.json")
    default_config_path = os.path.join(PROJECT_DIR, "config", "config.default.json")

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
