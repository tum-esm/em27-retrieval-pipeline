import json
import os
from rich.progress import track
from src import (
    export_to_files,
    generate_dataframes,
)
from src.helpers.utils import day_string_is_valid

# load config
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
with open(f"{PROJECT_DIR}/config.json") as f:
    config = json.load(f)

    # TODO: validate authentication config format

    # input settings
    assert day_string_is_valid(config["input"]["startDate"])
    assert day_string_is_valid(config["input"]["endDate"])
    assert set(config["input"]["gases"]).issubset(set(["co2", "ch4", "co"]))
    assert isinstance(config["input"]["locations"], list)
    assert all(isinstance(l, str) for l in config["input"]["locations"])

    # TODO: validate filter format

    # output settings
    assert isinstance(config["output"]["exportToCSV"], bool)
    assert isinstance(config["output"]["exportToJSON"], bool)
    assert isinstance(config["output"]["uploadToWebsite"], bool)
    if config["output"]["uploadToWebsite"]:
        assert config["output"]["exportToJSON"]

    # TODO: validate meta config format


def clear_upload_data(subdir, extension):
    d = f"{PROJECT_DIR}/data/{subdir}"
    filelist = [f for f in os.listdir(d) if f.endswith(extension)]
    for f in filelist:
        os.remove(f"{d}/{f}")


def run(day_strings):
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
        for day_string in track(day_strings, description="Uploading data to website"):
            # upload_to_cms.run(day_string)
            pass


if __name__ == "__main__":
    run(
        [
            str(d)
            for d in range(
                int(config["input"]["startDate"]), int(config["input"]["endDate"]) + 1
            )
            if day_string_is_valid(str(d))
        ]
    )
