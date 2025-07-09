from typing import Generator
import os
import shutil
import pytest
import tum_esm_utils
import src

_PROJECT_DIR = tum_esm_utils.files.rel_to_abs_path("..")


@pytest.fixture
def wrap_test_with_mainlock() -> Generator[None, None, None]:
    with src.utils.semaphores.with_automation_lock():
        yield


@pytest.fixture(scope="session")
def download_sample_data() -> Generator[None, None, None]:
    """Download sample data from https://syncandshare.lrz.de and
    extract it to the testing data directory. This is done only
    once per test run. The tar file will not be deleted afterwards
    and the download is skipped if the tar file already exists.

    The tar file has about 96MB."""

    testing_data_path = os.path.join(_PROJECT_DIR, "data", "testing", "inputs", "data")
    tarball_filename = "em27-retrieval-pipeline-test-interferograms-2024-09-17.tar.gz"

    # download testing data tarball if it does not exist
    if not os.path.isfile(os.path.join(testing_data_path, tarball_filename)):
        tum_esm_utils.shell.run_shell_command(
            "wget --quiet https://syncandshare.lrz.de/dl/"
            + f"fiEh5KjXeb8b715kU4cwWi/{tarball_filename}",
            working_directory=testing_data_path,
        )

    # remove existing input data
    if os.path.isdir(os.path.join(testing_data_path, "ifg")):
        shutil.rmtree(os.path.join(testing_data_path, "ifg"))

    # extract tarball
    tum_esm_utils.shell.run_shell_command(
        f"tar -xzf {tarball_filename}",
        working_directory=testing_data_path,
    )

    yield


@pytest.fixture(scope="session")
def provide_config_template() -> Generator[src.types.Config, None, None]:
    """Provide a temporary config used in profiles download."""

    config = src.types.Config.load(
        os.path.join(_PROJECT_DIR, "config", "config.template.json"),
        ignore_path_existence=True,
    )
    config.general.data.ground_pressure.path.root = "/tmp"
    config.general.data.atmospheric_profiles.root = "/tmp"
    config.general.data.interferograms.root = "/tmp"
    config.general.data.results.root = "/tmp"
    config.bundles = []
    config.profiles.scope.force_download_locations = []  # type: ignore

    yield config


@pytest.fixture(scope="function")
def remove_temporary_retrieval_data() -> Generator[None, None, None]:
    # remove all output data before test
    output_path = tum_esm_utils.files.rel_to_abs_path("../data/testing/container/outputs")
    for f in os.listdir(output_path):
        p = os.path.join(output_path, f)
        if os.path.isdir(p):
            shutil.rmtree(p)

    yield

    # remove all containers after test
    """container_path = tum_esm_utils.files.rel_to_abs_path("../data/containers")
    for f in os.listdir(container_path):
        p = os.path.join(container_path, f)
        if os.path.isdir(p):
            shutil.rmtree(p)"""
