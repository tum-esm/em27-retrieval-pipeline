import os
import subprocess


dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))

SRC = f"{PROJECT_DIR}/src/tueiesm_pylot_template.yml"


def run(site: str, date: str, config: dict):
    with open(SRC, "r") as f:
        file_content = "".join(f.readlines())

    replacements = {
        "SERIAL_NUMBER": str(config["sensor_serial_numbers"][site]).zfill(3),
        "SITE": site,
        "DATE": date,
        "PROJECT_DIR": PROJECT_DIR,
        "COMMIT_SHA": subprocess.check_output(
            ["git", "rev-parse", "--short", "--verify", "HEAD"]
        )
        .decode()
        .replace("\n", ""),
    }

    for key, value in replacements.items():
        file_content = file_content.replace(f"%{key}%", value)

    with open(f"{PROJECT_DIR}/inputs/{site}_{date}.yml", "w") as f:
        f.write(file_content)
