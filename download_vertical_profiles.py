import asyncio
import os
import json
import logging

from pathlib import Path
from filelock import FileLock

from src import utils
from src.types import Configuration, Location, Sensor


def run() -> None:

    logging.basicConfig(level=logging.INFO)

    try:

        project_path = Path(os.path.abspath(__file__)).parent

        # Load and parse the configuration
        config_path = os.path.join(project_path, "config", "config.json")
        with FileLock(config_path + ".lock", timeout=10), open(config_path, "r") as f:
            config = json.load(f, object_hook=lambda d: Configuration(**d))
            logging.info(f"Configuration ✅")

        # Request locations and sensors
        tasks = ["locations.json", "sensors.json"]
        urls = [os.path.join(config.location_data, task) for task in tasks]
        responses = asyncio.run(
            utils.git_request(urls, config.git_username, config.git_token)
        )

        # Parse locations and sensors
        for task, response in zip(tasks, responses):
            response.raise_for_status()

            if task == "locations.json":
                """locations = {
                "TUM_G": Location(details="...", lon=11.671, lat=48.261, alt=491),
                "TUM_I": Location(details="...", lon=11.569, lat=48.151, alt=539)}
                """
                locations: dict[str, Location] = {
                    location_tag: Location(**data)
                    for location_tag, data in response.json().items()
                }
                logging.info(f"Locations ✅")

            elif task == "sensors.json":
                """sensor_locations = {
                    "ma": (
                        Sensor(from_date=date(2019, 1, 1), to_date=date(2019, 31, 12), location="TUM_G",
                        Sensor(from_date=date(2020, 1, 1), to_date=date(2020, 31, 12), location="TUM_I"),
                    ...
                }
                """
                sensor_locations: dict[str, tuple[Sensor, ...]] = {
                    sensor_tag: tuple(Sensor(**data) for data in sensor["locations"])
                    for sensor_tag, sensor in response.json().items()
                }
                logging.info(f"Sensors ✅")

    except Exception as e:
        print(e)


if __name__ == "__main__":
    run()
