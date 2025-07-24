import json
from typing import Generator, Optional
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


def download_github_release_asset(
    repository: str,
    asset_name: str,
    dst_dir: str,
    final_name: Optional[str] = None,
    access_token: Optional[str] = None,
    force: bool = False,
) -> None:
    """Downloads a specific asset from the latest release of a GitHub repository.

    Args:
        repository:    In the format "owner/repo".
        asset_name:    The name of the asset to download.
        dst_dir:       The directory where the asset will be saved.
        final_name:    Optional final name for the downloaded asset. If None, uses `asset_name`.
        access_token:  The GitHub access token. Only required if the repo is private.
        force:         If True, forces the download even if the file already exists.
    """

    if final_name is None:
        final_name = asset_name
    if os.path.exists(os.path.join(dst_dir, final_name)) and not force:
        return

    try:
        releases = json.loads(
            tum_esm_utils.shell.run_shell_command(
                (
                    f"curl -L "
                    + f'-H "Accept: application/vnd.github+json" '
                    + (f'-H "Authorization: Bearer {access_token}" ' if access_token else "")
                    + ' -H "X-GitHub-Api-Version: 2022-11-28" '
                    + f"https://api.github.com/repos/{repository}/releases"
                )
            )
        )
    except:
        raise RuntimeError(
            f"Repository '{repository}' not found or access token does not have the required permissions."
        )

    if not isinstance(releases, list):
        raise RuntimeError(
            f"Failed to fetch releases from repository '{repository}'. Response: {releases}"
        )
    for release in releases:
        if not isinstance(release, dict):
            raise RuntimeError(
                f"Invalid release format in repository '{repository}'. Release: {releases}"
            )

    url: Optional[str] = None
    for o in sorted(releases, key=lambda x: x["published_at"], reverse=True):
        for asset in o["assets"]:
            if asset["name"] == asset_name:
                url = asset["url"]
                break
    if url is None:
        raise RuntimeError(
            f"Asset '{asset_name}' not found in any release of repository '{repository}'."
        )

    tum_esm_utils.shell.run_shell_command(
        f"curl -L "
        + (f'-H "Authorization: Bearer {access_token}" ' if access_token else "")
        + f'-H "Accept: application/octet-stream" '
        + f"-o {asset_name} "
        + url,
        working_directory=dst_dir,
    )
    if final_name != asset_name:
        final_path = os.path.join(dst_dir, final_name)
        if os.path.exists(final_path):
            os.remove(final_path)
        os.rename(os.path.join(dst_dir, asset_name), final_path)


@pytest.fixture(scope="session")
def download_sample_data() -> Generator[None, None, None]:
    """Download sample data from a GitHub release because it is too big for the repository.
    Could also be done with a Git LFS but this way it is easier to share for other purposes."""

    for label in ["interferograms", "atmospheric-profiles", "ground-pressure"]:
        download_github_release_asset(
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
