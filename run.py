import json
import os
from rich.progress import track
from src import export_to_files, generate_dataframes, upload_to_cms
from src.helpers.constants import ALL_GASES
from src.helpers.utils import day_string_is_valid

# load config
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
with open(f"{PROJECT_DIR}/config.json") as f:
    config = json.load(f)

    # MYSQL CONFIG
    assert (
        len(config["authentication"]["mysql"].keys()) <= 4
    ), f"config.authentication.mysql has unknown options"
    for key in ["host", "user", "passwd", "database"]:
        assert isinstance(
            config["authentication"]["mysql"][key], str
        ), f"config.authentication.mysql.{key} has to be string"

    # STRAPI CONFIG
    assert (
        len(config["authentication"]["strapi"].keys()) <= 3
    ), f"config.authentication.strapi has unknown options"
    for key in ["url", "apiKey"]:
        assert isinstance(
            config["authentication"]["strapi"][key], str
        ), f"config.authentication.strapi.{key} has to be string"

    # INPUT CONFIG
    assert day_string_is_valid(
        config["input"]["startDate"]
    ), "config.input.startDate has to be a valid date"
    assert day_string_is_valid(
        config["input"]["endDate"]
    ), "config.input.endDate has to be a valid date"
    assert (
        config["input"]["startDate"] <= config["input"]["endDate"]
    ), "config.input.startDate has to be before config.input.endDate"
    assert set(config["input"]["gases"]).issubset(
        set(ALL_GASES)
    ), f"config.input.gases has to be a subset of {ALL_GASES}"
    assert isinstance(
        config["input"]["locations"], list
    ), "config.input.locations has to be a list"
    assert all(
        isinstance(l, str) for l in config["input"]["locations"]
    ), "config.input.locations has to be a list of strings"

    # FILTER CONFIG
    assert isinstance(
        config["filter"]["movingWindowSizeMinutes"], int
    ), "config.filter.movingWindowSizeMinutes has to be integer"
    assert isinstance(
        config["filter"]["outputStepSizeMinutes"], int
    ), "config.filter.outputStepSizeMinutes has to be integer"
    assert isinstance(config["filter"]["cases"],
                      list), "config.filter.cases invalid"
    assert set(["outlier", "rollingMean"]).issubset(
        set(config["filter"]["cases"])
    ), 'config.filter.cases have to contain cases from of ["outlier", "rollingMean"]'
    assert set(config["filter"]["cases"]).issubset(
        set(["outlier", "rollingMean", "continuous", "interval"])
    ), 'config.filter.cases can only contain cases from ["outlier", "rollingMean", "continuous", "interval"]'

    # OUTPUT CONFIG
    assert isinstance(
        config["output"]["exportToCSV"], bool
    ), "config.output.exportToCSV has to be boolean"
    assert isinstance(
        config["output"]["exportToJSON"], bool
    ), "config.output.exportToJSON has to be boolean"
    assert isinstance(
        config["output"]["uploadToWebsite"], bool
    ), "config.output.uploadToWebsite has to be boolean"
    if config["output"]["uploadToWebsite"]:
        assert config["output"][
            "exportToJSON"
        ], "config.output.uploadToWebsite requires config.output.exportToJSON to be true"

    # CALIBRATION DAYS CONFIG
    assert isinstance(
        config["calibrationDays"]["exportToCSV"], bool
    ), "config.calibrationDays.exportToCSV has to be boolean"
    assert isinstance(
        config["calibrationDays"]["exportToJSON"], bool
    ), "config.calibrationDays.exportToJSON has to be boolean"

    # META CONFIG
    assert isinstance(
        config["meta"]["codeRepository"], str
    ), "config.meta.codeRepository has to be string"
    assert isinstance(
        config["meta"]["authors"], list
    ), "config.meta.authors has to be a list"
    for author in config["meta"]["authors"]:
        assert isinstance(
            author, dict), f"config.meta.authors can only contain dicts"
        assert isinstance(
            author["name"], str
        ), f"config.meta.authors[i].name has to be string"
        assert isinstance(
            author["email"], str
        ), f"config.meta.authors[i].email has to be string"


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
        upload_to_cms.run()


if __name__ == "__main__":
    run(
        [
            str(d)
            for d in range(
                int(config["input"]["startDate"]), int(
                    config["input"]["endDate"]) + 1
            )
            if day_string_is_valid(str(d))
        ]
    )
