import os
import json
import httpx
from .helpers.utils import load_json, ls_ext, unique
from rich.progress import track
from rich.console import Console

console = Console()

# same level as pyproject.toml
project_dir = "/".join(__file__.split("/")[:-2])
data_dir = f"{project_dir}/data"

with open(f"{project_dir}/config.json") as f:
    config = json.load(f)
    STRAPI = config["authentication"]["strapi"]

DATA_URL = f"{STRAPI['url']}/api/sensor-days"
HEADERS = {
    "Authorization": f"bearer {STRAPI['apiKey']}",
    "Content-Type": "application/json",
}


def upload_data(data):
    # data = {
    #     "sensor": *,
    #     "location": *,
    #     "gas": *,
    #     "date": "2021-08-01",
    #     "filteredCount": *,
    #     "filteredTimeseries": {"xs": *, "ys": *},
    #     "rawCount": *,
    #     "rawTimeseries": {"xs": *, "ys": *},
    #     "flagCount": *,
    #     "flagTimeseries": {"xs": *, "ys": *},
    # }

    r = httpx.post(
        DATA_URL,
        headers=HEADERS,
        data=json.dumps({"data": data}),
    )
    if r.status_code == 400:
        console.print(
            f'JSON format invalid: {r.json()["error"]["message"]}', style="bold red"
        )
    elif r.status_code != 200:
        raise Exception(f"automation is not behaving as expected: {r.json()}")


def run():
    # 1. determine days to be uploaded
    all_day_strings = unique(
        [
            s[:8]
            for s in ls_ext(f"{data_dir}/json-out", ".json")
            if s[:8].isnumeric() and len(s) == 13
        ]
    )

    # 2. upload all days
    for day_string in track(all_day_strings, description="Upload days to Strapi"):
        with open(f"{data_dir}/json-out/{day_string}.json", "r") as f:
            try:
                document = json.load(f)
                assert isinstance(document, list)
                assert all([isinstance(timeseries, dict) for timeseries in document])
                assert all(
                    [
                        timeseries["date"]
                        == f"{day_string[:4]}-{day_string[4:6]}-{day_string[6:]}"
                        for timeseries in document
                    ]
                )
                for timeseries in document:
                    upload_data(timeseries)
            except Exception as e:
                print(e)
                print(f"{day_string} could not be uploaded")
