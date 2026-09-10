import os
import pytest
import tum_esm_utils
import src
import dotenv

PROJECT_DIR = tum_esm_utils.files.rel_to_abs_path("../..")


@pytest.mark.em27_metadata_library
def test_remote_loader_public_repo() -> None:
    src.em27_metadata.load_from_github("tum-esm/em27-metadata")


@pytest.mark.em27_metadata_library
def test_remote_loader_private_repo() -> None:
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_file):
        dotenv.load_dotenv(env_file)
    access_token = os.getenv("TUM_ESM_GITHUB_ACCESS_TOKEN")
    # if access_token is None:
    #    pytest.skip("TUM_ESM_GITHUB_ACCESS_TOKEN not set as environment variable")
    assert access_token is not None
    src.em27_metadata.load_from_github("tum-esm/em27-metadata-storage", access_token=access_token)


@pytest.mark.em27_metadata_library
def test_local_loader() -> None:
    for v in ["toml", "json"]:
        src.em27_metadata.load_from_local_files(
            config_directory=os.path.join(PROJECT_DIR, "src", "em27_metadata", "sample_data", v),
        )
