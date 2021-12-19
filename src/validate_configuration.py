import os
import json
from src.helpers.constants import ALL_GASES
from src.helpers.utils import day_string_is_valid

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run():
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
        assert isinstance(
            config["filter"]["cases"], list
        ), "config.filter.cases invalid"
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
                author, dict
            ), f"config.meta.authors can only contain dicts"
            assert isinstance(
                author["name"], str
            ), f"config.meta.authors[i].name has to be string"
            assert isinstance(
                author["email"], str
            ), f"config.meta.authors[i].email has to be string"
