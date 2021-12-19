import json
import os
from rich.progress import track
from src import (
    export_to_files,
    generate_dataframes,
    upload_to_cms,
    validate_configuration,
)
from src.helpers.utils import day_string_is_valid

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
        dataframes = generate_dataframes.run(day_string)
        if config["output"]["exportToCSV"]:
            export_to_files.as_csv(
                day_string,
                dataframes[
                    "withCalibrationDays"
                    if config["calibrationDays"]["exportToCSV"]
                    else "withoutCalibrationDays"
                ],
            )
        if config["output"]["exportToJSON"]:
            export_to_files.as_json(
                day_string,
                dataframes[
                    "withCalibrationDays"
                    if config["calibrationDays"]["exportToJSON"]
                    else "withoutCalibrationDays"
                ],
            )

    if config["output"]["uploadToWebsite"]:
        for day_string in track(day_strings, description="Upload data to CMS"):
            upload_to_cms.run(day_string)


if __name__ == "__main__":
    run_pipeline(
        [
            str(d)
            for d in range(
                int(config["input"]["startDate"]), int(config["input"]["endDate"]) + 1
            )
            if day_string_is_valid(str(d))
        ]
    )
