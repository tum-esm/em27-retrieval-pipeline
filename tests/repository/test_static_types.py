import os
import shutil
import sys
import pytest
import tum_esm_utils

PROJECT_DIR = tum_esm_utils.files.rel_to_abs_path("../../")


def _rmdir(path: str) -> None:
    path = os.path.join(PROJECT_DIR, path)
    if os.path.isdir(path):
        shutil.rmtree(path)


@pytest.mark.order(1)
@pytest.mark.quick
def test_static_types() -> None:
    os.system(f"cd {PROJECT_DIR} && rm -f .mypy_cache/3.*/cli.*")
    _rmdir(".mypy_cache/3.11/src")
    _rmdir(".mypy_cache/3.11/tests")

    for call in [
        "mypy -p src",
        "mypy -p tests",
        "mypy cli.py",
        "mypy src/retrieval/algorithms/proffast-1.0/main/prfpylot/main.py",
        "mypy src/scripts",
    ]:
        assert os.system(f"cd {PROJECT_DIR} && {sys.executable} -m {call}") == 0
