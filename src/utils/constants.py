from datetime import datetime
import json
import os
from src.utils import functions

PROJECT_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
with open(f"{PROJECT_DIR}/config.json") as f:
    CONFIG = json.load(f)

UNITS = {
    "co2": "ppm",
    "ch4": "ppm",
    "co": "ppb",
}

# These are the locations where each spectrometer has been used permanently.
# On calibration days spectrometers where move to other places. On these calibration
# days, the data should not be used in the resulting CSV
DEFAULT_SPECTROMETERS = {
    "HAW": "mb86",
    "GEO": "me17",
    "ROS": "md16",
    "JOR": "mc15",
    "TUM_I": "ma61",
    "OBE": "md16",
    "GRÄ": "mc15",
    "FEL": "mb86",
    "TAU": "me17",
}

PHYSICAL_FILTER_SETTINGS = {
    "fvsi_threshold": 5,  # fractional variation in solar intensity
    "sia_threshold": 0.4,  # solar intensity average
    "sza_threshold": 75,  # solar zenith angle
    "o2_error": 0.0005,
    "step_size": 0.1,
    "flag": 1,  # a 0 means "ignore all errors (flags) from gfit"
}

REPLACEMENT_DICT = {
    "AUTHOR_NAMES": ", ".join(
        list(map(lambda a: a["name"], CONFIG["meta"]["authors"]))
    ),
    "CONTACT_EMAILS": ", ".join(
        list(map(lambda a: a["email"], CONFIG["meta"]["authors"]))
    ),
    "GENERATION_DATE": str(datetime.now()) + " UTC",
    "CODE_REPOSITORY": CONFIG["meta"]["codeRepository"],
    "COMMIT_SHA": functions.get_commit_sha(),
    "COMMENT": CONFIG["output"]["comment"],
    "SETTING_fvsi_thold": PHYSICAL_FILTER_SETTINGS["fvsi_threshold"],
    "SETTING_sia_thold": PHYSICAL_FILTER_SETTINGS["sia_threshold"],
    "SETTING_sza_thold": PHYSICAL_FILTER_SETTINGS["sza_threshold"],
    "SETTING_o2_error": PHYSICAL_FILTER_SETTINGS["o2_error"],
    "SETTING_step_size": PHYSICAL_FILTER_SETTINGS["step_size"],
    "SETTING_flag": PHYSICAL_FILTER_SETTINGS["flag"],
    "SETTING_moving_window_size_minutes": str(
        CONFIG["filter"]["movingWindowSizeMinutes"]
    ),
    "SETTING_output_step_size_minutes": str(CONFIG["filter"]["outputStepSizeMinutes"]),
    "SETTING_filter_cases": str(CONFIG["filter"]["cases"]),
}

ALL_GASES = ["co2", "ch4", "co"]
ALL_SENSORS = ["ma", "mb", "mc", "md", "me"]
