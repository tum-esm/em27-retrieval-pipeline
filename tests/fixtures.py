import os
import shutil
from typing import Generator
import pytest
import tum_esm_utils
from src import types, utils

_PROJECT_DIR = tum_esm_utils.files.rel_to_abs_path("..")


@pytest.fixture
def wrap_test_with_mainlock() -> Generator[None, None, None]:
    with utils.semaphores.with_automation_lock():
        yield


@pytest.fixture(scope="session")
def download_sample_data() -> Generator[None, None, None]:
    """Download sample data from https://syncandshare.lrz.de and
    extract it to the testing data directory. This is done only
    once per test run. The tar file will not be deleted afterwards
    and the download is skipped if the tar file already exists.

    The tar file has about 96MB."""

    testing_data_path = os.path.join(
        _PROJECT_DIR, "data", "testing", "container"
    )
    tarball_filename = "em27-retrieval-pipeline-test-inputs-1.0.0.tar.gz"

    # download testing data tarball if it does not exist
    if not os.path.isfile(os.path.join(testing_data_path, tarball_filename)):
        tum_esm_utils.shell.run_shell_command(
            f"wget --quiet https://syncandshare.lrz.de/dl/" +
            f"fiUY18aZDWf3CYNisatQB9/{tarball_filename}",
            working_directory=testing_data_path,
        )

    # remove existing input data
    for input_dir in [
        os.path.join(testing_data_path, "inputs", t)
        for t in ["log", "map", "ifg"]
    ]:
        if os.path.isdir(input_dir):
            shutil.rmtree(input_dir)

    # extract tarball
    tum_esm_utils.shell.run_shell_command(
        f"tar -xzf {tarball_filename}",
        working_directory=testing_data_path,
    )

    yield


@pytest.fixture(scope="session")
def provide_config_template() -> Generator[types.Config, None, None]:
    """Provide a temporary config used in profiles download."""

    config = types.Config.load(
        os.path.join(_PROJECT_DIR, "config", "config.template.json"),
        ignore_path_existence=True,
    )
    config.general.data.datalogger.root = "/tmp"
    config.general.data.atmospheric_profiles.root = "/tmp"
    config.general.data.interferograms.root = "/tmp"
    config.general.data.results.root = "/tmp"
    config.export_targets = []

    yield config


@pytest.fixture(scope="function")
def remove_temporary_retrieval_data() -> Generator[None, None, None]:
    # remove all output data before test
    output_path = tum_esm_utils.files.rel_to_abs_path(
        "../data/testing/container/outputs"
    )
    for f in os.listdir(output_path):
        p = os.path.join(output_path, f)
        if os.path.isdir(p):
            shutil.rmtree(p)

    yield

    # remove all containers after test
    container_path = tum_esm_utils.files.rel_to_abs_path("../data/containers")
    for f in os.listdir(container_path):
        p = os.path.join(container_path, f)
        if os.path.isdir(p):
            shutil.rmtree(p)
