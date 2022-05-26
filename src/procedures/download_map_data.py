import json
import os

from src.utils.load_config import load_config


dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
CONFIG = load_config()


def run(session):
    sensor = str(session["sensor"])
    date = str(session["date"])

    # TODO: upgrade download-map-data project
    # TODO: use sensor identifier
    dst_dir = f"{PROJECT_DIR}/inputs/{session['sensor']}_map"
    download_config = {
        "lat": session["lat"],
        "lng": session["lon"],
        "dates": [date],
        "user": CONFIG["download_map_data_email"],
        "dst": dst_dir,
        "downloadTypes": {"map": True, "mod": False},
        "minimumDaysDelay": 5,
        "downloadTimeoutSeconds": 120,
    }
    with open(f"{PROJECT_DIR}/download-map-data/config.json", "w") as f:
        json.dump(download_config, f)

    os.system(f"{PROJECT_DIR}/.venv/bin/python {PROJECT_DIR}/download-map-data/run.py")
    assert os.path.isfile(f"{dst_dir}/L1{date}.map"), "Map file download not successful"
    os.rename(f"{dst_dir}/L1{date}.map", f"{dst_dir}/{session['sensor']}{date}.map")
