from pathlib import PosixPath
from typing import Optional, Union
import os
import re
import yaml


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
            f for f in files
            if (is_directory == os.path.isdir(os.path.join(path, f)))
        ]
    if is_file is not None:
        files = [
            f for f in files
            if (is_file == os.path.isfile(os.path.join(path, f)))
        ]

    return files


def read_yaml(
        file_path: Union[str, PosixPath]
) -> dict[str, str]:
    with open(file_path, 'r') as f:
        return dict(yaml.load(f, Loader=yaml.FullLoader))
