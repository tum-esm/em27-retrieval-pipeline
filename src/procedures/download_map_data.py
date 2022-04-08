import json
import os
import shutil


dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))


def run(site: str, date: str, config: dict):

    # create/empty output directory
    dst_dir = f"{PROJECT_DIR}/inputs/{site}_map"
    if os.path.isdir(dst_dir):
        shutil.rmtree(dst_dir)
    os.mkdir(dst_dir)

    download_config = {
        "lat": config["sensor_coordinates"][site]["lat"],
        "lng": config["sensor_coordinates"][site]["lng"],
        "dates": [f"20{date}"],
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

    assert os.path.isfile(
        f"{dst_dir}/L120{date}.map"
    ), "Map file download not successful"

    os.rename(f"{dst_dir}/L120{date}.map", f"{dst_dir}/{site}20{date}.map")
