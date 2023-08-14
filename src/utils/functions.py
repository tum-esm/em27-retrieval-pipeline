import os
import re
from typing import Optional


def list_directory(
    path: str,
    regex: Optional[str] = None,
    is_directory: Optional[bool] = None,
    is_file: Optional[bool] = None,
) -> list[str]:
    assert os.path.isdir(path), f"Path {path} is not a directory"
    files = os.listdir(path)
    if regex is not None:
        files = [f for f in files if re.match(regex, f)]
    if is_directory is not None:
        files = [
            f for f in files if (is_directory == os.path.isdir(os.path.join(path, f)))
        ]
    if is_file is not None:
        files = [f for f in files if (is_file == os.path.isfile(os.path.join(path, f)))]

    return files


def get_coordinates_slug(lat: float, lon: float, verbose: bool = False) -> str:
    """Return a slug for the location

    verbose = false: `48N011E``
    verbose = true: `48.00N_11.00E`"""

    lat = round(lat)
    lon = round(lon)

    str_ = f"{abs(lat):.2f}" if verbose else f"{abs(lat):02}"
    str_ += "S" if lat < 0 else "N"
    str_ += "_" if verbose else ""
    str_ += f"{abs(lon):.2f}" if verbose else f"{abs(lon):03}"
    return str_ + ("W" if lon < 0 else "E")
