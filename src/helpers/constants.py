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
