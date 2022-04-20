import os
import subprocess
import time
from src import utils

dir = os.path.dirname
PROJECT_DIR = dir(dir(os.path.abspath(__file__)))


def _upload(user):
    result = subprocess.run(
        ["bash", f"{PROJECT_DIR}/upload_request.sh"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ.copy(), "PASSWD": user},
    )
    if result.returncode == 0:
        return "ok"
    elif "Access failed: 553" in result.stderr.decode():
        return "access"
    else:
        return result.stderr.decode()


def run(date: str = None, config: dict = None):
    # Write request file
    with open(f"input_file.txt", "w") as f:
        f.write(
            "\n".join(
                [
                    "L1",
                    date,
                    date,
                    str(round(config["lat"])),
                    str(round(config["lng"])),
                    config["user"],
                ]
            )
        )

    utils.print_blue(date, "MAP/MOD", "Uploading request")
    try_a = _upload(config["user"])
    if try_a == "ok":
        os.remove("input_file.txt")
        return True

    if try_a != "access":
        utils.print_red(date, "MAP/MOD", f"Uploading request failed: {try_a}")
        return False

    utils.print_blue(
        date, "MAP/MOD", "Rate limiting or missing data, retrying once in 1 minute"
    )
    time.sleep(60)

    try_b = _upload(config["user"])
    os.remove("input_file.txt")
    if try_b == "ok":
        return True

    if try_b != "access":
        utils.print_red(date, "MAP/MOD", f"Uploading request failed: {try_a}")
    else:
        utils.print_blue(date, "MAP/MOD", "Missing data, skipping this date")
    return False
