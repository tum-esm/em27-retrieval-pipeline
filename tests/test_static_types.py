import os
import shutil
import pytest
import tum_esm_utils

PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=2)


def _rmdir(path: str) -> None:
    path = os.path.join(PROJECT_DIR, path)
    if os.path.isdir(path):
        shutil.rmtree(path)


@pytest.mark.order(1)
@pytest.mark.ci_quick
@pytest.mark.ci_intensive
@pytest.mark.ci_complete
def test_static_types() -> None:
    _rmdir(".mypy_cache/3.11/src")
    _rmdir(".mypy_cache/3.11/tests")

    for path in [
        "src/run_automated_proffast.py",
        "src/download_atmospheric_profiles.py",
        "tests/",
        "src/export_retrieval_outputs.py",
        "src/retrieval/proffast-1.0/main/prfpylot/main.py",
    ]:
        assert os.system(f"cd {PROJECT_DIR} && .venv/bin/python -m mypy {path}") == 0
