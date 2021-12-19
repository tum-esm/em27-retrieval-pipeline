import os
import json
import mysql.connector
import pandas as pd
from rich.console import Console
from src import validate_configuration

console = Console()

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT_PATH = f"{PROJECT_DIR}/automatic-report.json"

with open(f"{PROJECT_DIR}/config.json") as f:
    config = json.load(f)
    validate_configuration.run()
    LOCATIONS = config["input"]["locations"]


def generate_report():
    connection = mysql.connector.connect(**config["authentication"]["mysql"])
    df = pd.read_sql(
        f"""
        SELECT Date, ID_Location, COUNT(*)
        FROM measuredValues
        WHERE (Date >= '{config["input"]["startDate"]}') AND
        (Date <= '{config["input"]["endDate"]}') AND
        (ID_Location in ({', '.join([repr(l) for l in LOCATIONS])}))
        GROUP BY Date, ID_Location
        ORDER BY Count(*) DESC
        """,
        con=connection,
    )
    connection.close()

    report = {s: {} for s in LOCATIONS}
    for index, row in df.iterrows():
        report[str(row["ID_Location"])][str(row["Date"])] = int(row["COUNT(*)"])

    return report


def get_dates_to_be_updated(old_report, new_report):
    dates_to_be_updated = {}
    for s in LOCATIONS:
        for d in new_report[s].keys():
            if d not in old_report[s]:
                old_report[s][d] = 0
            if new_report[s][d] != old_report[s][d]:
                if d not in dates_to_be_updated:
                    dates_to_be_updated[d] = {}
                dates_to_be_updated[d][s] = f"{old_report[s][d]} -> {new_report[s][d]}"
    return dates_to_be_updated


def run():
    with console.status("[bold green]Updating report"):
        # collect current state in MySQL and state at last automatic run
        new_report = generate_report()
        if os.path.exists(REPORT_PATH):
            with open(REPORT_PATH) as f:
                old_report = json.load(f)
        else:
            old_report = {s: {} for s in LOCATIONS}

        # overwrite old report with new report
        with open(REPORT_PATH, "w") as f:
            json.dump(new_report, f, indent=4)

        # compare reports and determine changed dates
        dates_to_be_updated = get_dates_to_be_updated(old_report, new_report)

    return dates_to_be_updated
