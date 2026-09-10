import os
import pytest
import src
import dotenv

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.mark.em27_metadata_library
def test_remote_loader_public_repo() -> None:
    src.em27_metadata.load_from_github("tum-esm/em27-metadata")


@pytest.mark.em27_metadata_library
def test_remote_loader_private_repo() -> None:
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_file):
        dotenv.load_dotenv(env_file)
    access_token = os.getenv("TUM_ESM_GITHUB_ACCESS_TOKEN")
    if access_token is None:
        pytest.skip("TUM_ESM_GITHUB_ACCESS_TOKEN not set as environment variable")
    src.em27_metadata.load_from_github("tum-esm/em27-metadata-storage", access_token=access_token)


@pytest.mark.em27_metadata_library
def test_local_loader() -> None:
    src.em27_metadata.load_from_local_files(
        locations_path=os.path.join(PROJECT_DIR, "data", "locations.json"),
        sensors_path=os.path.join(PROJECT_DIR, "data", "sensors.json"),
        campaigns_path=os.path.join(PROJECT_DIR, "data", "campaigns.json"),
    )
