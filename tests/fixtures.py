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
    """Download sample data from https://syncandshare.lrz.de and
    extract it to the testing data directory. This is done only
    once per test run. The tar file will not be deleted afterwards
    and the download is skipped if the tar file already exists.

    The tar file has about 96MB."""

    testing_data_path = os.path.join(PROJECT_DIR, "data", "testing", "container")
    tarball_filename = "automated-proffast-pylot-example-inputs.tar.gz"

    # download testing data tarball if it does not exist
    if not os.path.isfile(os.path.join(testing_data_path, tarball_filename)):
        tum_esm_utils.shell.run_shell_command(
            f"wget --quiet https://syncandshare.lrz.de/dl/"
            + f"fiA9bjdafNcuVGrmMfDL49/{tarball_filename}",
            working_directory=testing_data_path,
        )

    # remove existing input data
    for input_dir in [
        os.path.join(testing_data_path, "inputs", t) for t in ["log", "map", "ifg"]
    ]:
        if os.path.isdir(input_dir):
            shutil.rmtree(input_dir)

    # extract tarball
    tum_esm_utils.shell.run_shell_command(
        f"tar -xf {tarball_filename}",
        working_directory=testing_data_path,
    )

    yield


@pytest.fixture(scope="function")
def clear_output_data() -> Generator[None, None, None]:
    """Remove all directories in the testing output directory"""

    testing_data_output_dir = os.path.join(
        PROJECT_DIR, "data", "testing", "container", "outputs"
    )
    for d in os.listdir(testing_data_output_dir):
        subdir = os.path.join(testing_data_output_dir, d)
        if os.path.isdir(subdir):
            shutil.rmtree(subdir)

    yield


"""
@pytest.fixture(scope="session")
def provide_export_config() -> Generator[custom_types.Config, None, None]:
    # Provide a temporary config file that points to the export testing data.

    # LOAD CONFIG TEMPLATE

    config_template = tum_esm_utils.files.load_json_file(
        os.path.join(PROJECT_DIR, "config", "config.template.json")
    )

    # UPDATE INPUTS

    config_template["general"]["data_dst_dirs"]["results"] = os.path.join(
        PROJECT_DIR, "data", "testing", "merging", "raw"
    )

    # UPDATE OUTPUTS

    config_template["output_merging_targets"][0]["dst_dir"] = os.path.join(
        PROJECT_DIR, "data", "testing", "merging", "merged"
    )

    # PARSE CONFIG OBJECT

    config = custom_types.Config(**config_template)

    # RUN TEST

    yield config
"""


@pytest.fixture(scope="session")
def provide_config_template() -> Generator[custom_types.Config, None, None]:
    """Provide a temporary config used in profiles download."""

    config = custom_types.Config(
        **tum_esm_utils.files.load_json_file(
            os.path.join(PROJECT_DIR, "config", "config.template.json")
        )
    )
    config.general.data_src_dirs.datalogger = "/tmp"
    config.general.data_src_dirs.vertical_profiles = "/tmp"
    config.general.data_src_dirs.interferograms = "/tmp"
    config.general.data_dst_dirs.results = "/tmp"
    config.output_merging_targets = []

    yield config
