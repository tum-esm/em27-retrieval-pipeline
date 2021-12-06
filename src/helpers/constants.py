from datetime import datetime
import json
import os
from src.helpers.utils import get_commit_sha

PROJECT_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
with open(f"{PROJECT_DIR}/config.json") as f:
    config = json.load(f)

UNITS = {
    "co2": "ppm",
    "ch4": "ppm",
    "co": "ppb",
}

# These are the locations where each sensor has been used permanently.
# On calibration days sensors where move to other places. On these calibration
# days, the data should not be used in the resulting CSV
SETUPS = [
    ("HAW", "mb86"),
    ("GEO", "me17"),
    ("ROS", "md16"),
    ("JOR", "mc15"),
    ("TUM_I", "ma61"),
    ("OBE", "md16"),
    ("GRÄ", "mc15"),
    ("FEL", "mb86"),
    ("TAU", "me17"),
]

FILTER_SETTINGS = {
    "fvsi_threshold": 5,  # fractional variation in solar intensity
    "sia_threshold": 0.4,  # solar intensity average
    "sza_threshold": 75,  # solar zenith angle
    "o2_error": 0.0005,
    "step_size": 0.1,
    "flag": 1,  # a 0 means "ignore all errors (flags) from gfit"
    "cluster_start": 4,  # Time in UTC, start time for the use of measurements
    "cluster_end": 18,  # Time in UTC, end time for the use of measurements
}

REPLACEMENT_DICT = {
    "AUTHOR_NAMES": ", ".join(
        list(map(lambda a: a["name"], config["meta"]["authors"]))
    ),
    "CONTACT_EMAILS": ", ".join(
        list(map(lambda a: a["email"], config["meta"]["authors"]))
    ),
    "GENERATION_DATE": str(datetime.datetime.now()) + " UTC",
    "CODE_REPOSITORY": config["meta"]["codeRepository"],
    "COMMIT_SHA": get_commit_sha(),
    "SETTING_fvsi_thold": FILTER_SETTINGS["fvsi_threshold"],
    "SETTING_sia_thold": FILTER_SETTINGS["sia_threshold"],
    "SETTING_sza_thold": FILTER_SETTINGS["sza_threshold"],
    "SETTING_o2_error": FILTER_SETTINGS["o2_error"],
    "SETTING_step_size": FILTER_SETTINGS["step_size"],
    "SETTING_flag": FILTER_SETTINGS["flag"],
}
