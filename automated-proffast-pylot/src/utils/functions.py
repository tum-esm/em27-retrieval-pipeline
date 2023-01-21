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