from datetime import datetime
import os

import numpy as np


def get_dir_name(path: str) -> str:
    return os.path.basename(os.path.dirname(path))


def get_file_name(path: str) -> str:
    return os.path.basename(path)


def convert_date_to_numpy(date_as_string: str) -> np.datetime64:
    return np.datetime64(datetime.strptime(date_as_string, "%Y%m%d").date())
