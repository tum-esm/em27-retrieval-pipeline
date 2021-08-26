from dotenv import load_dotenv
import os
from rich.console import Console
from rich.progress import track
import json
import sys
import datetime

console = Console()

# same level as pyproject.toml
project_dir = "/".join(__file__.split("/")[:-1])
with open(f"{project_dir}/config.json") as f:
    config = json.load(f)
    assert type(config["faunaKey"]) == str
    assert type(config["firestoreKeyFile"]) == str
    os.environ["FIRESTORE_KEY_FILE"] = f"{project_dir}/" + config["firestoreKeyFile"]
    os.environ["FAUNA_DB_KEY"] = config["faunaKey"]

from src.update_report import run as update_report
from src.process_website_data.run import (
    update_dataframe_for_website,
)  # nopep8
from src.upload_website_data.run import upload  # nopep8


def clear_upload_data():
    for sd in ["csv-in", "csv-out", "json-out", "meta-out"]:
        d = f"{project_dir}/src/upload_website_data/data/{sd}"
        filelist = [
            f for f in os.listdir(d) if f.endswith(".json") or f.endswith(".csv")
        ]
        for f in filelist:
            os.remove(f"{d}/{f}")


def log(message: str):
    with open("automation.log", "a") as f:
        f.write(str(datetime.datetime.now()) + " UTC - " + message + "\n")


def run_automatic():
    dates = update_report()
    clear_upload_data()

    if len(dates) > 0:
        log("-" * 40)
        log("Starting automatic plot generation")
        log("-" * 40)

        print(f"Updating {len(dates.keys())} days: {list(dates.keys())}")

        for date in track(dates, description="Applying plot filters"):
            log(f"{date}: {dates[date]}")
            update_dataframe_for_website(
                date,
                f"{project_dir}/src/upload_website_data/data/csv-in/",
                one_day=True,
            )
        upload(dates)
    else:
        log("-" * 40)
        log("Automation found no new data to be plotted")
        log("-" * 40)


run_automatic()
