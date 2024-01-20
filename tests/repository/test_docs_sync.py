import sys
import pytest
import tum_esm_utils

_PROJECT_DIR = tum_esm_utils.files.rel_to_abs_path("../..")


def _get_checksum() -> str:
    # credits to https://stackoverflow.com/a/545413/8255842
    return tum_esm_utils.shell.run_shell_command(
        "find docs/pages docs/components -type f -print0 | sort -z | xargs -0 sha1sum | sha1sum",
        working_directory=_PROJECT_DIR,
    )


@pytest.mark.order(2)
@pytest.mark.quick
def test_api_reference_state() -> None:
    checksum_before = _get_checksum()
    tum_esm_utils.shell.run_shell_command(
        f"{sys.executable} docs/scripts/sync_api_reference.py",
        working_directory=_PROJECT_DIR,
    )
    checksum_after = _get_checksum()
    assert checksum_before == checksum_after, "API reference is out of sync"
