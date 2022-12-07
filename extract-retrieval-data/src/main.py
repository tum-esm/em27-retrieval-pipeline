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

    # Request data and build query list
    query_list, stations = procedures.build_query_list(
        request_config=config.request, location_data_config=config.location_data
    )

    # TODO: for every date in campaign dates produce one CSV;
    #       all code below in this loop ("per CSV file"). Only
    #       dates between config.request.from_date and .to_date
    #       should be considered

    # for all stations that were at their correct location at
    # this date, query the database
    # df = procedures.get_daily_dataframe(
    #    config.database, "2.2", ["ma", "mb"], "20210109"
    # )
    # TODO: df does not have the same columns (should have all
    #       NaN columns for all stations of that campaign)

    # print(df)
    # df.to_csv("some.csv")
