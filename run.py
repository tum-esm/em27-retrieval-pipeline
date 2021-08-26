from dotenv import load_dotenv
import os
from rich.console import Console
from rich.progress import track

console = Console()
# same level as pyproject.toml
project_dir = "/".join(__file__.split("/")[:-1])
assert ".env" in os.listdir(project_dir)
load_dotenv(dotenv_path=f"{project_dir}/.env")
assert os.getenv("FAUNA_DB_KEY") != None
assert os.getenv("FIRESTORE_KEY_FILE") != None

import sys
import datetime
from tqdm import tqdm

from src.process_website_data import run as process_website_data  # nopep8
from src.upload_website_data.run import upload  # nopep8
from src import update_report


def clear_upload_data():
    for sd in ["csv-in", "csv-out", "json-out", "meta-out"]:
        d = f"{project_dir}/src/upload_website_data/data/{sd}"
        filelist = [
            f for f in os.listdir(d) if f.endswith(".json") or f.endswith(".csv")
        ]
        for f in filelist:
            os.remove(f"{d}/{f}")


def run(date):
    clear_upload_data()

    # get data from server and upload to FaunaDB
    process_website_data.update_dataframe_for_website(
        date, f"{project_dir}/src/upload_website_data/data/csv-in/", one_day=True
    )
    upload([date])


def run_all():
    for month in range(1, 9):
        clear_upload_data()

        print(f"month {month}")
        for day in tqdm(range(1, 32)):
            # try-except needed sind not all days have 31 days -> error in function
            try:
                process_website_data.update_dataframe_for_website(
                    f"2021{month:02d}{day:02d}",
                    f"{project_dir}/src/upload_website_data/data/csv-in/",
                    one_day=True,
                )
            except:
                print("no data")

        upload([f"2021{month:02d}{day:02d}" for day in range(1, 32)])


def run_selected(dates):
    log("-" * 40)
    log("Starting automation")
    log("-" * 40)
    clear_upload_data()

    print(f"Updating {len(dates.keys())} days: {list(dates.keys())}")

    for date in track(dates, description="Applying plot filters"):
        log(f"{date}: {dates[date]}")
        process_website_data.update_dataframe_for_website(
            date,
            f"{project_dir}/src/upload_website_data/data/csv-in/",
            one_day=True,
        )
    upload(dates)


def log(message: str):
    with open("automation.log", "a") as f:
        f.write(str(datetime.datetime.now()) + " UTC - " + message + "\n")


if __name__ == "__main__":
    # run(f"20190913")
    # run_all()
    # run_selected(update_report.run())
    pass
