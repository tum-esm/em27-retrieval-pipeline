import os
import json
from pathlib import Path
from filelock import FileLock

from src import custom_types, procedures

PROJECT_PATH = Path(os.path.abspath(__file__)).parents[1]


def run() -> None:

    # Load and parse configuration
    config_path = os.path.join(PROJECT_PATH, "config", "config.json")
    with FileLock(config_path + ".lock", timeout=10), open(config_path, "r") as f:
        config = custom_types.Configuration(**json.load(f))

    # Request campaign data
    campaign, locations, sensors = procedures.get_campaign_data(
        request_config = config.request,
        location_data_config = config.location_data
    )
    
    print(campaign, locations, sensors)
    
    
