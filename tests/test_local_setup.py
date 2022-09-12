import os
import pytest

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))


@pytest.mark.integration
def test_local_setup():
    assert os.path.isfile(
        f"{PROJECT_DIR}/.venv/bin/python"
    ), "virtual environment does not exist"

    assert os.path.isfile(
        f"{PROJECT_DIR}/location-data/.gitignore"
    ), "please run fetch-location-data.py first"

    assert os.path.isfile(
        f"{PROJECT_DIR}/src/prfpylot/prfpylot/pylot.py"
    ), f"submodule src/prfpylot not initialized"

    assert all(
        [
            os.path.isfile(x)
            for x in [
                f"{PROJECT_DIR}/src/prfpylot/prf/preprocess/preprocess4",
                f"{PROJECT_DIR}/src/prfpylot/prf/pcxs20",
                f"{PROJECT_DIR}/src/prfpylot/prf/invers20",
            ]
        ]
    ), f"proffast is not fully compiled"
