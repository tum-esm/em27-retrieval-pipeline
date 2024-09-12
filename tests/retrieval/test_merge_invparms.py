import glob
import os
import pytest
import tum_esm_utils
import src

_PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=3)
_TESTDATA_PATH = os.path.join(_PROJECT_DIR, "data/testing/inputs/raw_invparms")


@pytest.mark.order(3)
@pytest.mark.quick
def test_merge_invparms_files() -> None:
    filepaths = glob.glob(os.path.join(_TESTDATA_PATH, "*invparms.dat"))
    assert len(filepaths) == 3

    individual_dfs = [
        src.retrieval.utils.invparms_files.read_and_merge_invparms_files([filepath])
        for filepath in filepaths
    ]
    assert all([df is not None for df in individual_dfs])

    merged_df = src.retrieval.utils.invparms_files.read_and_merge_invparms_files(filepaths)
    assert merged_df is not None

    assert sum([len(df) for df in individual_dfs if df is not None]) == len(merged_df)
