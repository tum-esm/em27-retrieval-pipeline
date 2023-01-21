from datetime import datetime
import os
import subprocess
from typing import Optional


dirname = os.path.dirname
PROJECT_DIR = dirname(dirname(dirname(os.path.abspath(__file__))))


def get_commit_sha() -> Optional[str]:
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "--short", "--verify", "HEAD"],
                cwd=PROJECT_DIR,
            )
            .decode()
            .replace("\n", "")
        )
    except:
        return None


def load_file(path: str) -> str:
    with open(path, "r") as f:
        return "".join(f.readlines())


def dump_file(path: str, content: str) -> None:
    with open(path, "w") as f:
        f.write(content)


def insert_replacements(content: str, replacements: dict[str, str]) -> str:
    for key, value in replacements.items():
        content = content.replace(f"%{key}%", value)
    return content


def is_date_string(date_string: str) -> bool:
    try:
        datetime.strptime(date_string, "%Y%m%d")
        return True
    except (AssertionError, ValueError):
        return False


def date_is_too_recent(
    date_string: str,
    min_days_delay: int = 1,
) -> bool:
    date_object = datetime.strptime(
        date_string, "%Y%m%d"
    )  # will have the time 00:00:00
    return (datetime.now() - date_object).days >= min_days_delay
