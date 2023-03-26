import os
import shutil
from typing import Generator
import filelock
import pytest
import tum_esm_utils
from src import custom_types, utils


# TODO: syncronize mainlock names across codebase
PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=2)
lock = filelock.FileLock(os.path.join(PROJECT_DIR, "src", "main.lock"), timeout=0)


@pytest.fixture
def wrap_test_with_mainlock() -> Generator[None, None, None]:
    try:
        lock.acquire()
        yield
        lock.release()
    except filelock.Timeout:
        raise Exception("automation is already running")


@pytest.fixture(scope="session")
def download_sample_data() -> Generator[None, None, None]:
    """Download sample data from syncandshare and extract it to the
    testing data directory. This is done only once per test run."""

    testing_data_path = os.path.join(PROJECT_DIR, "data", "testing")
    tarball_filename = "automated-proffast-pylot-example-inputs.tar.gz"

    # download testing data tarball if it does not exist
    if not os.path.isfile(os.path.join(testing_data_path, tarball_filename)):
        utils.run_shell_command(
            f"wget --quiet https://syncandshare.lrz.de/dl/"
            + "fiA9bjdafNcuVGrmMfDL49/{tarball_filename}",
            working_directory=testing_data_path,
        )

    # extract tarball
    utils.run_shell_command(
        f"tar -xf {tarball_filename}",
        working_directory=testing_data_path,
    )

    # copy data to correct testing locations
    for s, d in [
        ("inputs", "container"),
        ("inputs/ifg", "pipeline/interferograms"),
        ("inputs/log", "pipeline/datalogger"),
        ("inputs/map", "pipeline/vertical_profiles"),
    ]:
        if os.path.isdir(f"{testing_data_path}/{d}"):
            shutil.rmtree(f"{testing_data_path}/{d}")
        utils.run_shell_command(
            f"cp -r {testing_data_path}/{s}/* {testing_data_path}/{d}",
            working_directory=testing_data_path,
        )

    # remove extracted tarball data
    shutil.rmtree(os.path.join(testing_data_path, "inputs"))

    yield


@pytest.fixture(scope="function")
def provide_tmp_config() -> Generator[custom_types.Config, None, None]:
    """Create a temporary config file that points to the testing data.
    This is done before each test; the original config file is restored
    afterwards."""

    config_path = os.path.join(PROJECT_DIR, "config", "config.json")
    config_template_path = os.path.join(PROJECT_DIR, "config", "config.template.json")

    # backup original config to restore it later
    tmp_config_path = os.path.join(PROJECT_DIR, "config", "config.tmp.json")
    assert not os.path.isfile(tmp_config_path), f'"{tmp_config_path}" should not exist'
    if os.path.isfile(config_path):
        os.rename(config_path, tmp_config_path)

    # create temporary config where all directories point to the testing data
    config_template = tum_esm_utils.files.load_json_file(config_template_path)
    for key in ["datalogger", "vertical_profiles", "interferograms"]:
        config_template["general"]["data_src_dirs"][key] = os.path.join(
            PROJECT_DIR, "data", "testing", "pipeline", key
        )
    # enable automatic probessing in config
    config_template["general"]["data_dst_dirs"]["results"] = os.path.join(
        PROJECT_DIR, "data", "testing", "pipeline", "results_raw"
    )
    config_template["output_merging_targets"][0]["dst_dir"] = os.path.join(
        PROJECT_DIR, "data", "testing", "pipeline", "results_merged"
    )
    tum_esm_utils.files.dump_json_file(config_path, config_template)

    # run test
    yield custom_types.Config(**config_template)

    # possibly restore original config
    os.remove(config_path)
    if os.path.isfile(tmp_config_path):
        os.rename(tmp_config_path, config_path)
