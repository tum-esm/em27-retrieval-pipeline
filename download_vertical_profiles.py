import os
import re
import json
import logging
import asyncio

from io import BytesIO
from ftplib import FTP

from pathlib import Path
from filelock import FileLock
from datetime import datetime, timedelta

from src import utils, types
from src import QueryList

# NOTE - dst_dir rename
# NOTE - camelCase
# NOTE - globally share config
# NOTE - Check slug <0


def run() -> None:

    logging.basicConfig(level=logging.INFO)

    try:

        project_path = Path(os.path.abspath(__file__)).parent

        # Load and parse the configuration
        camel_to_snake = re.compile(r"(?<!^)(?=[A-Z])")
        config_path = os.path.join(project_path, "config", "config.json")
        with FileLock(config_path + ".lock", timeout=10), open(config_path, "r") as f:
            config: types.Configuration = json.load(
                fp=f,
                object_hook=lambda cfg: types.Configuration(
                    # Convert camelCase to snake_case
                    **{
                        (camel_to_snake.sub("_", key).lower()): value
                        for key, value in cfg.items()
                    }
                ),
            )

        # Request locations and sensors
        urls = [
            os.path.join(config.location_data, task)
            for task in ("locations.json", "sensors.json")
        ]
        locations_response, sensors_response = asyncio.run(
            utils.get_git_urls(urls, config.git_username, config.git_token)
        )

        # Parse locations
        locations: dict[str, types.Location] = {
            location_tag: types.Location(**data)
            for location_tag, data in locations_response.json().items()
        }

        # Parse sensors and build query lists
        query_lists: dict[str, QueryList] = {}
        for sensor, data in sensors_response.json().items():
            for interval in data["locations"]:

                from_date = datetime.strptime(interval["from_date"], "%Y%m%d").date()
                to_date = datetime.strptime(interval["to_date"], "%Y%m%d").date()

                # Remove sensor locations outside of the requested range
                start = max(from_date, config.from_date)
                end = min(to_date, config.to_date)
                if start <= end:

                    lat = round(locations[interval["location"]].lat)
                    lon = round(locations[interval["location"]].lon)
                    lat_lon = str(lat) + "\n" + str(lon)

                    if lat_lon not in query_lists:
                        query_lists[lat_lon] = QueryList(
                            str(abs(lat)).zfill(2)
                            + ("S_" if lat < 0 else "N_")
                            + str(abs(lon)).zfill(3)
                            + ("W" if lon < 0 else "E")
                        )
                    query_lists[lat_lon].insert(sensor, start, end)

        # Optimize query lists and request data
        for lat_lon, query_list in query_lists.items():
            query_list.optimize(config.dst_directory)
            with FTP(
                host="ccycle.gps.caltech.edu",
                user="anonymous",
                passwd=config.email,
                timeout=60,
            ) as ftp:

                ftp.cwd("upload")
                ftp.set_debuglevel(9)
                for query in query_list:

                    site = query.sensors.pop()
                    bio = BytesIO(
                        "\n".join(
                            (
                                site,
                                datetime.strftime(query.start, "%Y%m%d"),
                                datetime.strftime(
                                    query.end + timedelta(1), "%Y%m%d"
                                ),  # FIXME -  Exclusive?
                                lat_lon,
                                config.email,
                            )
                        ).encode("utf-8")
                    )
                    # ftp.storbinary("STOR input_file_2020.txt", bio)
                    # äftp.storbinary("STOR input_file.txt", bio)

                    # Group and do multiple requests by renaming input.txt?

                    # Features: CRONJOB IF FAILED AUTO, LOG

    except Exception as e:
        print(e)


if __name__ == "__main__":
    run()
