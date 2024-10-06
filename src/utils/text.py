import datetime
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


def replace_regex_placeholders(
    regex_pattern: str,
    sensor_id: str,
    date: datetime.date,
) -> tuple[re.Pattern[str], re.Pattern[str]]:
    """Replace placeholders in a regex pattern.
    
    Returns: tuple[pattern of any matching file, pattern of the file of the given date]"""

    general_regex = regex_pattern
    specific_regex = regex_pattern

    date_string = date.strftime("%Y%m%d")
    for placeholder, specific_replacement, general_replacement in [
        ("$(SENSOR_ID)", sensor_id, sensor_id),
        ("$(DATE)", date_string, "\\d{8}"),
        ("$(YYYY)", date_string[: 4], "\\d{4}"),
        ("$(YY)", date_string[2 : 4], "\\d{2}"),
        ("$(MM)", date_string[4 : 6], "\\d{2}"),
        ("$(DD)", date_string[6 :], "\\d{2}"),
    ]:
        general_regex = general_regex.replace(placeholder, general_replacement)
        specific_regex = specific_regex.replace(placeholder, specific_replacement)

    return re.compile(general_regex), re.compile(specific_regex)
