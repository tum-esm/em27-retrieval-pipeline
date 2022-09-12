import os
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
