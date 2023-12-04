from typing import Generator
import contextlib
import filelock
import tum_esm_utils


@contextlib.contextmanager
def with_automation_lock() -> Generator[None, None, None]:
    """This function will lock the automation with a file lock so that
    only one instance can run at a time.
    
    Usage:
    
    ```python
    with with_automation_lock():
        run_automation()
        # or
        run_tests()
    ```"""

    lock_path = tum_esm_utils.files.rel_to_abs_path("../../automation.lock")
    automation_lock = filelock.FileLock(lock_path, timeout=0)

    try:
        with automation_lock:
            yield
    except filelock.Timeout:
        print(f'locked by another process via file at path "{lock_path}"')
        raise TimeoutError("automation is already running")
