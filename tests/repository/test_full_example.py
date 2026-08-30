import pytest
import tum_esm_utils

PROJECT_DIR = tum_esm_utils.files.rel_to_abs_path("../../")


@pytest.mark.order(4)
@pytest.mark.ci
def test_full_example() -> None:
    tum_esm_utils.shell.run_shell_command(f"cd {PROJECT_DIR}/example && bash run.sh")
