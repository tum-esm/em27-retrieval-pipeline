import json
import os
from rich.progress import track
from src import (
    script_1_generate_dataframes,
    script_2_export_to_files,
    script_3_upload_to_cms,
)
from src.helpers import utilities, validate_configuration

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
with open(f"{PROJECT_DIR}/config.json") as f:
    config = json.load(f)
    validate_configuration.run()


def clear_upload_data(subdir, extension):
    d = f"{PROJECT_DIR}/data/{subdir}"
    filelist = [f for f in os.listdir(d) if f.endswith(extension)]
    for f in filelist:
        os.remove(f"{d}/{f}")


def run_pipeline(day_strings):
    for day_string in track(day_strings, description="Removing existing output files"):
        if config["output"]["exportToCSV"]:
            clear_upload_data("csv-out", f"{day_string}.csv")

        if config["output"]["exportToJSON"]:
            clear_upload_data("json-out", f"{day_string}.json")

    for day_string in track(day_strings, description="Extracting and exporting data"):
        dataframes = script_1_generate_dataframes.run(day_string)[
            "withCalibrationDays"
            if config["calibrationDays"]["exportToCSV"]
            else "withoutCalibrationDays"
        ]

        if dataframes is None:
            print(f"No data for {day_string}")
        else:
            if config["output"]["exportToCSV"]:
                script_2_export_to_files.as_csv(day_string, dataframes)
            if config["output"]["exportToJSON"]:
                script_2_export_to_files.as_json(day_string, dataframes)

    if config["output"]["uploadToWebsite"]:
        for day_string in track(day_strings, description="Upload data to CMS"):
            script_3_upload_to_cms.run(day_string)


if __name__ == "__main__":
    run_pipeline(
        [
            str(d)
            for d in range(
                int(config["input"]["startDate"]), int(config["input"]["endDate"]) + 1
            )
            if utilities.day_string_is_valid(str(d))
        ]
    )
