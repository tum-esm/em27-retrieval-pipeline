import os
import pytest
import tum_esm_utils

PROJECT_DIR = tum_esm_utils.files.rel_to_abs_path("../../")


@pytest.mark.order(4)
@pytest.mark.complete
def test_full_example() -> None:
    exit_code = os.system(f"cd {PROJECT_DIR}/example && bash run.sh")  # pyright: ignore[reportDeprecated]
    assert exit_code == 0, f"Full example failed with exit code {exit_code}"
