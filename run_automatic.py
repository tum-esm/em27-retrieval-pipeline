import json
import os
import datetime
from src.helpers import validate_configuration
from run import run_pipeline
from src.helpers import update_automation_report

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
with open(f"{PROJECT_DIR}/config.json") as f:
    config = json.load(f)
    validate_configuration.run()


def log(message: str):
    with open(f"{PROJECT_DIR}/automation.log", "a") as f:
        f.write(str(datetime.datetime.now()) + " UTC - " + message + "\n")


if __name__ == "__main__":
    dates = update_automation_report.run(update_report_file=False)
    if len(dates) > 0:
        log("Starting automatic data extraction")

        print(f"Updating {len(dates.keys())} day(s): {list(dates.keys())}")
        for date in dates.keys():
            log(f"{date}: {dates[date]}")

        try:
            run_pipeline(dates.keys())
            update_automation_report.run(update_report_file=True)
        except Exception as e:
            log(f"execution failed: {e}")
        log("-" * 40)
    else:
        log("Automation found no new data to be processed")
        log("-" * 40)
