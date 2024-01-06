import pytest
import requests
import tum_esm_utils


@pytest.mark.order(3)
@pytest.mark.quick
def test_ils_parameter_sync() -> None:
    url = "https://gitlab.eudat.eu/coccon-kit/proffastpylot/-/raw/master/prfpylot/ILSList.csv?ref_type=heads"
    r = requests.get(url)
    assert r.status_code == 200
    remote_file_content = r.text.strip("\n\t ")

    with open(
        tum_esm_utils.files.
        rel_to_abs_path("../../src/retrieval/utils/ils-parameters.csv")
    ) as f:
        local_file_content = f.read().strip("\n\t ")

    assert remote_file_content == local_file_content.strip("\n\t ")
