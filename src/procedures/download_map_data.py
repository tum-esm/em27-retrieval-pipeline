import json
import os


dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))


def run(sensor: str, date: str, config: dict):
    dst_dir = f"{PROJECT_DIR}/inputs/{sensor}/map"
    download_config = {
        "lat": config["coordinates"][sensor]["lat"],
        "lng": config["coordinates"][sensor]["lng"],
        "dates": [date],
        "user": config["download_map_data_email"],
        "dst": dst_dir,
        "downloadMap": True,
        "downloadMod": False,
        "minimumDaysDelay": 5,
        "downloadTimeoutSeconds": 120,
    }
    with open(f"{PROJECT_DIR}/download-map-data/config.json", "w") as f:
        json.dump(download_config, f)

    os.system(f"{PROJECT_DIR}/.venv/bin/python {PROJECT_DIR}/download-map-data/run.py")
    assert os.path.isfile(f"{dst_dir}/L1{date}.map"), "Map file download not successful"
    os.rename(f"{dst_dir}/L1{date}.map", f"{dst_dir}/{sensor}{date}.map")
