import datetime
import os
from src import types, utils

def find_pressure_files(
    root_dir: str,
    sensor_id: float,
    file_regex: str,
    date: datetime.date,
) -> tuple[list[str], list[str], list[str]]:
    """Find pressure files for a given sensor and date.
    
    Returns: tuple[list of all files for that sensor, list of all files following the given pattern, list of all matching files for that date]"""

    d = os.path.join(root_dir, sensor_id)
    if not os.path.exists(d):
        return [], []

    all_files = sorted(os.listdir(d))

    general_file_pattern, specific_file_pattern = utils.text.replace_regex_placeholders(
        file_regex, sensor_id, date
    )

    general_matching_files = [f for f in all_files if general_file_pattern.match(f) is not None]
    specific_matching_files = [f for f in all_files if specific_file_pattern.match(f) is not None]

    return all_files, general_matching_files, specific_matching_files


def pressure_files_exist(
    root_dir: str,
    sensor_id: float,
    file_regex: str,
    date: datetime.date,
) -> bool:
    """Check if pressure files for a given sensor and date exist. Like `find_pressure_files`, but more efficient. Use in the retrieval queue.
    
    Returns: bool indicating if any matching files exist. """

    d = os.path.join(root_dir, sensor_id)
    try:
        _, specific_file_pattern = utils.text.replace_regex_placeholders(
            file_regex, sensor_id, date
        )
        return any([specific_file_pattern.match(f) is not None for f in os.listdir(d)])
    except FileNotFoundError:
        return False

