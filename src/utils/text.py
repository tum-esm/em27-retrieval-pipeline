import datetime
import random
import re


def get_coordinates_slug(lat: float, lon: float, verbose: bool = False) -> str:
    """Return a slug for the location

    verbose = false: `48N011E``
    verbose = true: `48.00N_11.00E`"""

    latv = str(round(abs(lat)))
    latd = "S" if lat < 0 else "N"
    lonv = str(round(abs(lon)))
    lond = "W" if lon < 0 else "E"

    if verbose:
        return f"{latv}.00{latd}_{lonv}.00{lond}"
    else:
        return f"{latv.zfill(2)}{latd}{lonv.zfill(3)}{lond}"


def replace_regex_placeholders(regex_pattern: str, sensor_id: str, date: datetime.date) -> str:
    """Replace placeholders in a regex pattern"""

    date_string = date.strftime("%Y%m%d")
    for placeholder, replacement in [
        ("$(SENSOR_ID)", sensor_id),
        ("$(DATE)", date_string),
        ("$(YYYY)", date_string[: 4]),
        ("$(YY)", date_string[2 : 4]),
        ("$(MM)", date_string[4 : 6]),
        ("$(DD)", date_string[6 :]),
    ]:
        regex_pattern = regex_pattern.replace(placeholder, replacement)

    return regex_pattern
