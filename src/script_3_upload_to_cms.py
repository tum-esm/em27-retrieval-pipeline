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


def upload_day(day_object, day_url, headers):
    r = httpx.post(
        day_url,
        headers=headers,
        data=day_object,
    )
    if r.status_code == 500:
        print(f"{day_object['date']} - day already exists")
        try:
            r = httpx.get(
                day_url + f"?date={day_object['date']}",
                headers=headers,
            )
            assert r.status_code == 200
            assert len(r.json()) == 1
            assert len(r.json()) == 1
            r = httpx.put(
                day_url + f"/{r.json()[0]['_id']}",
                headers=headers,
                data=day_object,
            )
            assert r.status_code == 200
        except AssertionError as e:
            raise Exception(f"backend is not behaving as expected: {e}")
    elif r.status_code != 200:
        raise Exception(f"automation is not behaving as expected: {r.json()}")


def run():
    auth_url = f"{config['strapi']['url']}/auth/local"
    day_url = f"{config['strapi']['url']}/plot-days"
    meta_url = f"{config['strapi']['url']}/{config['strapi']['meta-endpoint']}"

    # 1. authorize client
    r = httpx.post(
        auth_url,
        data={
            "identifier": config["strapi"]["identifier"],
            "password": config["strapi"]["password"],
        },
        timeout=10,
    )
    if r.status_code != 200:
        raise Exception("could not authorize the client, invalid identifier/password")

    headers = {
        "Authorization": f"bearer {r.json()['jwt']}",
    }

    # 2. determine days to be uploaded
    all_day_strings = unique(
        [
            s[:8]
            for s in ls_ext(f"{data_dir}/json-out", ".json")
            if s[:8].isnumeric() and len(s) == 13
        ]
    )
    valid_day_strings = []

    # 3. upload all days
    for day_string in track(all_day_strings, description="Upload days to Strapi"):
        with open(f"{data_dir}/json-out/{day_string}.json", "r") as f:
            try:
                upload_day(json.load(f), day_url, headers)
                valid_day_strings.append(day_string)
            except Exception as e:
                print(f"{day_string} could not be uploaded: {e}")

    # 4. update meta document
    r = httpx.get(meta_url, headers=headers, timeout=10)
    if r.status_code != 200:
        raise Exception("meta could not be fetched")
    meta = r.json()["data"]
    r = httpx.put(
        meta_url,
        headers=headers,
        data={
            "data": {
                **meta,
                "gases": config["gases"],
                "stations": config["stations"],
                "days": list(sorted(unique(meta["days"] + valid_day_strings))),
            }
        },
        timeout=10,
    )
    assert r.status_code == 200
