import pytest
import tum_esm_utils


@pytest.mark.order(3)
@pytest.mark.integration
def test_system_packages() -> None:
    tum_esm_utils.shell.run_shell_command("unzip --help")
    tum_esm_utils.shell.run_shell_command("gfortran --help")
    tum_esm_utils.interferograms.detect_corrupt_ifgs(
        tum_esm_utils.files.rel_to_abs_path("."),
    )
