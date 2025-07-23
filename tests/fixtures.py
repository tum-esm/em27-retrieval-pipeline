from typing import Generator
import os
import shutil
import pytest
import tum_esm_utils
import src

_PROJECT_DIR = tum_esm_utils.files.rel_to_abs_path("..")
_TEST_DATA_DIR = os.path.join(_PROJECT_DIR, "data", "testing", "inputs", "data")


@pytest.fixture
def wrap_test_with_mainlock() -> Generator[None, None, None]:
    with src.utils.semaphores.with_automation_lock():
        yield


@pytest.fixture(scope="session")
def download_sample_data() -> Generator[None, None, None]:
    """Download sample data from a GitHub release because it is too big for the repository.
    Could also be done with a Git LFS but this way it is easier to share for other purposes."""

    for label in ["interferograms", "atmospheric-profiles", "ground-pressure"]:
        tum_esm_utils.code.download_github_release_asset(
            repository="tum-esm/em27-retrieval-pipeline",
            asset_name=f"em27-retrieval-pipeline-tests-data-20250723-{label}.tar.gz",
            dst_dir=_TEST_DATA_DIR,
            final_name=f"{label}.tar.gz",
        )
        tum_esm_utils.shell.run_shell_command(
            f"tar -xzf {label}.tar.gz", working_directory=_TEST_DATA_DIR
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
