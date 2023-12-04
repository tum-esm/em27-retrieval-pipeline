import contextlib
from typing import Generator, Optional
import os
import re
import filelock

import tum_esm_utils


def list_directory(
    path: str,
    regex: Optional[str] = None,
    is_directory: Optional[bool] = None,
    is_file: Optional[bool] = None,
) -> list[str]:
    assert os.path.isdir(path), f"Path {path} is not a directory"
    files = os.listdir(path)
    if regex is not None:
        files = [f for f in files if re.match(regex, f)]
    if is_directory is not None:
        files = [
            f for f in files
            if (is_directory == os.path.isdir(os.path.join(path, f)))
        ]
    if is_file is not None:
        files = [
            f for f in files
            if (is_file == os.path.isfile(os.path.join(path, f)))
        ]

    return files


def get_coordinates_slug(lat: float, lon: float, verbose: bool = False) -> str:
    """Return a slug for the location

    verbose = false: `48N011E``
    verbose = true: `48.00N_11.00E`"""

    lat = round(lat)
    lon = round(lon)

    str_ = f"{abs(lat):.2f}" if verbose else f"{abs(lat):02}"
    str_ += "S" if lat < 0 else "N"
    str_ += "_" if verbose else ""
    str_ += f"{abs(lon):.2f}" if verbose else f"{abs(lon):03}"
    return str_ + ("W" if lon < 0 else "E")


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
