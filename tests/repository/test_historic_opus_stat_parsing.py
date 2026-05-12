import os
import sys
import pytest
import tum_esm_utils

PROJECT_DIR = tum_esm_utils.files.rel_to_abs_path("../../")


@pytest.mark.order(3)
@pytest.mark.quick
def test_historic_opus_stat_parsing() -> None:
    assert (
        os.system(  # pyright: ignore[reportDeprecated]
            f"cd {PROJECT_DIR} && {sys.executable} src/scripts/parse_historic_opus_file_stats.py --force"
        )
        == 0
    )
