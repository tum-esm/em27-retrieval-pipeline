import glob
import os
import tum_esm_utils
from src import utils

_PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=3)
_TESTDATA_PATH = os.path.join(_PROJECT_DIR, "data/testing/pylot")


def test_merge_invparms_files() -> None:
    filepaths = glob.glob(os.path.join(_TESTDATA_PATH, "*invparms.dat"))

    individual_dfs = [
        utils.proffast.read_and_merge_invparms_files([filepath])
        for filepath in filepaths
    ]
    merged_df = utils.proffast.read_and_merge_invparms_files(filepaths)

    assert sum([len(df) for df in individual_dfs]) == len(merged_df)
