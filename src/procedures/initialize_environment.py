import os
import shutil
import subprocess


dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
YAML_TEMPLATE = f"{PROJECT_DIR}/src/pylot_config_template.yml"


def run(config: dict, sensor: str):
    assert os.path.isfile(
        f"{PROJECT_DIR}/.venv/bin/python"
    ), "Virtual environment does not exist"

    assert os.path.isfile(
        f"{PROJECT_DIR}/download-map-data/run.py"
    ), "Module download-map-data not initialized"

    assert os.path.isfile(
        f"{PROJECT_DIR}/proffastpylot/prfpylot/pylot.py"
    ), "Module proffastpylot not initialized"

    assert all(
        [
            os.path.isfile(x)
            for x in [
                f"{PROJECT_DIR}/proffastpylot/prf/preprocess/preprocess4",
                f"{PROJECT_DIR}/proffastpylot/prf/pcxs20",
                f"{PROJECT_DIR}/proffastpylot/prf/invers20",
            ]
        ]
    ), "PROFFAST not compiled completely"

    # Clear directories "inputs" and "outputs"
    for _d in ["inputs", "outputs"]:
        shutil.rmtree(f"{PROJECT_DIR}/{_d}")
        os.mkdir(f"{PROJECT_DIR}/{_d}")
        os.system(f"touch {PROJECT_DIR}/{_d}/.gitkeep")
    os.mkdir(f"{PROJECT_DIR}/inputs/{sensor}_ifg")
    os.mkdir(f"{PROJECT_DIR}/inputs/{sensor}_map")
    os.mkdir(f"{PROJECT_DIR}/inputs/{sensor}_pressure")

    # Create 'coords.csv' file
    with open(f"{PROJECT_DIR}/inputs/coords.csv", "w") as _f:
        _f.write("Site, Latitude, Longitude, Altitude_kmasl, Starttime\n")
        for _sensor, _coords in config["coordinates"].items():
            _f.write(
                ", ".join(
                    [
                        _sensor,
                        str(round(_coords["lat"], 3)),
                        str(round(_coords["lng"], 3)),
                        str(round(_coords["alt"] / 1000, 3)),
                        "2019-01-01",
                    ]
                )
                + "\n"
            )

    # Create YAML file for proffast
    with open(YAML_TEMPLATE, "r") as _f:
        file_content = "".join(_f.readlines())

    replacements = {
        "SERIAL_NUMBER": str(config["serial_numbers"][sensor]).zfill(3),
        "SENSOR": sensor,
        "PROJECT_DIR": PROJECT_DIR,
        "COMMIT_SHA": subprocess.check_output(
            ["git", "rev-parse", "--short", "--verify", "HEAD"]
        )
        .decode()
        .replace("\n", ""),
    }

    for key, value in replacements.items():
        file_content = file_content.replace(f"%{key}%", value)

    with open(f"{PROJECT_DIR}/inputs/{sensor}-pylot-config.yml", "w") as _f:
        _f.write(file_content)
