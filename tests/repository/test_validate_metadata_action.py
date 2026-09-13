import os
import subprocess
import sys

import pytest
import tum_esm_utils

PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=3)


@pytest.mark.quick
def test_action_can_import_metadata_as_a_standalone_package() -> None:
    source_directory = os.path.join(PROJECT_DIR, "src")
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys\nsys.path.insert(0, sys.argv[1])\nimport em27_metadata",
            source_directory,
        ],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
