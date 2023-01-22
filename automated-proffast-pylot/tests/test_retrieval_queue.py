import json
import os
import pytest
from src import custom_types, interfaces, utils
from .fixtures import provide_tmp_config
import dotenv

dir = os.path.dirname
PROJECT_DIR = dir(dir(os.path.abspath(__file__)))
dotenv.load_dotenv(os.path.join(PROJECT_DIR, "tests", ".env"))


@pytest.mark.ci
def test_retrieval_queue(provide_tmp_config) -> None:
    with open(os.path.join(PROJECT_DIR, "config", "config.template.json"), "r") as f:
        config_file_content = json.load(f)
    config_file_content["data_src_dirs"]["datalogger"] = os.path.join(
        PROJECT_DIR, "example", "inputs", "log"
    )
    config_file_content["data_src_dirs"]["vertical_profiles"] = os.path.join(
        PROJECT_DIR, "example", "inputs", "map"
    )
    config_file_content["data_src_dirs"]["interferograms"] = os.path.join(
        PROJECT_DIR, "example", "inputs", "ifg"
    )
    config_file_content["data_dst_dirs"]["results"] = os.path.join(
        PROJECT_DIR, "example", "outputs"
    )

    config_file_content["location_data"]["github_repository"] = os.environ[
        "LOCATION_DATA_GITHUB_REPOSITORY"
    ]
    config_file_content["location_data"]["access_token"] = os.environ[
        "LOCATION_DATA_ACCESS_TOKEN"
    ]

    config = custom_types.Config(**config_file_content)
    logger = utils.Logger("testing", print_only=True)

    retrieval_queue = interfaces.RetrievalQueue(config, logger)

    next_item_1 = retrieval_queue.get_next_item()
    print(f"next_item_1: {next_item_1}")
    assert next_item_1.sensor_id == "mc"
    assert next_item_1.date == "20220602"

    next_item_2 = retrieval_queue.get_next_item()
    print(f"next_item_2: {next_item_2}")
    assert next_item_2 is None
