import os
import json
import httpx
from .helpers.utils import load_json, ls_ext, unique
from rich.progress import track

# same level as pyproject.toml
project_dir = "/".join(__file__.split("/")[:-2])
data_dir = f"{project_dir}/data"

with open(f"{project_dir}/config.json") as f:
    config = json.load(f)
    assert type(config["strapi"]) == dict
    for key in ["identifier", "password", "url", "meta-endpoint"]:
        assert type(config["strapi"][key]) == str


def run():

    auth_url = f"{config['strapi']['url']}/auth/local"
    day_url = f"{config['strapi']['url']}/plot-days"
    meta_url = f"{config['strapi']['url']}/{config['strapi']['meta-endpoint']}"

    r = httpx.post(
        auth_url,
        data={
            "identifier": config["strapi"]["identifier"],
            "password": config["strapi"]["password"],
        },
        timeout=10,
    )
    # TODO: Add exception for unsuccessful authentication
    # print(r.status_code)
    headers = {
        "Authorization": f"bearer {r.json()['jwt']}",
    }

    r = httpx.post(
        day_url,
        headers=headers,
        data={"date": "20202020", "data": {"some-day": "over the ocean"}},
    )
    print(r)
    return

    all_day_strings = unique(
        [
            s[:8]
            for s in ls_ext(f"{data_dir}/json-out", ".json")
            if s[:8].isnumeric() and len(s) == 13
        ]
    )
    # all_day_strings = ['20201214', ...]
    invalid_day_strings = []

    # Upload all days
    for day_string in track(all_day_strings, description="Upload days to Strapi"):
        with open(f"{data_dir}/json-out/{day_string}.json", "r") as f:
            dayObject = json.load(f)
            try:
                # TODO: Upload dayObject to strapi
                pass
            except:
                invalid_day_strings.append(day_string)

    # TODO: Download meta from strapi
    # TODO: append added_days to meta.days
    # TODO: Upload meta to strapi
