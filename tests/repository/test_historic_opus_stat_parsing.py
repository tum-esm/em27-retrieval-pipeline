import os
import shutil
import sys
import time
import pytest
import tum_esm_utils

PROJECT_DIR = tum_esm_utils.files.rel_to_abs_path("../../")


@pytest.mark.order(3)
@pytest.mark.quick
def test_historic_opus_stat_parsing() -> None:
    git_status_before = tum_esm_utils.shell.run_shell_command("git status")
    print(git_status_before)
    assert (
        os.system(
            f"cd {PROJECT_DIR} && {sys.executable} src/scripts/parse_historic_opus_file_stats.py --force"
        )
        == 0
    )
    time.sleep(1)
    git_status_after = tum_esm_utils.shell.run_shell_command("git status")
    print(git_status_after)
    assert git_status_before == git_status_after, "Git status changed after running the script."
