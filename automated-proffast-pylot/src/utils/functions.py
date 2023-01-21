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
