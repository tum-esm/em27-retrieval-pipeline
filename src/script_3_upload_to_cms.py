import os
import sys
import json
import time
import httpx
import threading
import queue
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


class MonitoredThread(threading.Thread):
    def __init__(self, data, bucket):
        threading.Thread.__init__(self)
        self.data = data
        self.bucket = bucket

    def run(self):
        try:
            upload_data(self.data)
        except Exception:
            self.bucket.put(sys.exc_info())


def upload_data(data):
    thread_label = f"thread {data['date']}.{data['gas']}.{data['spectrometer']}"
    failed_attempts = 0

    while True:
        try:
            r = httpx.post(
                DATA_URL, headers=HEADERS, data=json.dumps({"data": data}), timeout=60
            )
            if r.status_code == 400:
                raise Exception(
                    f'JSON format invalid in {thread_label}: {r.json()["error"]["message"]}'
                )
            assert r.status_code == 200, r.json()
            return
        except (AssertionError, json.decoder.JSONDecodeError) as e:
            failed_attempts += 1
            if failed_attempts > 4:
                raise Exception(
                    f"automation is not behaving as expected in {thread_label}: {e}"
                )
            else:
                # sleeping for 15 seconds until the upload is tried again
                time.sleep(15)


def run(day_string):
    exceptionQueue = queue.Queue()

    file_path = f"{data_dir}/json-out/{day_string}.json"
    if os.path.isfile(file_path):
        with open(f"{data_dir}/json-out/{day_string}.json", "r") as f:
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
            print(f"{day_string} ({len(document)} timeseries)")
            threads = [
                MonitoredThread(timeseries, exceptionQueue) for timeseries in document
            ]
            for t in threads:
                t.start()
            for t in threads:
                try:
                    exc = exceptionQueue.get(block=False)
                except queue.Empty:
                    t.join()
                else:
                    exc_type, exc_obj, exc_trace = exc
                    print(exc_type, exc_obj)
                    raise Exception(f"{exc_type}: {exc_obj}, {exc_trace}")
