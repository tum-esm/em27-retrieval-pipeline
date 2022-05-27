import json
import os
import download_profiles_main

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))


def run(query):
    d = f'{PROJECT_DIR}/dataset/{query["sensor"]}{query["serial_number"]}'
    if not os.path.isdir(d):
        os.mkdir(d)
    with open(f"{PROJECT_DIR}/config.json", "r") as f:
        c = json.load(f)
        c["stationId"] = query["sensor"]
        c["lat"] = query["lat"]
        c["lon"] = query["lon"]
        c["dates"] = [f'{query["from"]}-{query["to"]}']
        c["dst"] = d

    with open(f"{PROJECT_DIR}/config.json", "w") as f:
        json.dump(c, f)
    
    download_profiles_main.main()
