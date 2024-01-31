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
    remote_ILS_lines = set(remote_file_content.split("\n"))

    for local_path in [
        "../../src/retrieval/utils/ils-parameters.csv",
        "../../src/retrieval/algorithms/proffast-2.2/main/prfpylot/ILSList.csv",
        "../../src/retrieval/algorithms/proffast-2.2/main/prfpylot/ILSList.csv"
    ]:
        with open(tum_esm_utils.files.rel_to_abs_path(local_path)) as f:
            local_file_content = f.read().strip("\n\t ")

        local_ILS_lines = set(local_file_content.split("\n"))
        lines_missing_locally = remote_ILS_lines.difference(local_ILS_lines)
        assert len(
            lines_missing_locally
        ) == 0, f"Missing lines in {local_path}: {lines_missing_locally}"
