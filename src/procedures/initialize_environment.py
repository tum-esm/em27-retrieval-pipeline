import os
import shutil
import subprocess


dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
YAML_TEMPLATE = f"{PROJECT_DIR}/src/tueiesm_pylot_template.yml"


def run(config: dict):
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

    # Clear directory "inputs" and "outputs"
    for d in ["inputs", "outputs"]:
        for f in os.listdir(f"{PROJECT_DIR}/{d}"):
            filepath = f"{PROJECT_DIR}/{d}/{f}"
            if os.path.isdir(filepath):
                shutil.rmtree(filepath)
            else:
                if not filepath.endswith(".gitkeep"):
                    os.remove(filepath)

    # Make sure all input- and output-directories exist
    for sensor in config["sensors_to_consider"]:
        sensor_input_dir = f"{PROJECT_DIR}/inputs/{sensor}"
        if not os.path.isdir(sensor_input_dir):
            os.mkdir(sensor_input_dir)
        sensor_output_dir = f"{PROJECT_DIR}/outputs/{sensor}"
        if not os.path.isdir(sensor_output_dir):
            os.mkdir(sensor_output_dir)
        for d in ["ifg", "map", "pressure"]:
            if not os.path.isdir(f"{sensor_input_dir}/{d}"):
                os.mkdir(f"{sensor_input_dir}/{d}")

    # Update/create 'coords.csv' file
    with open(f"{PROJECT_DIR}/inputs/coords.csv", "w") as f:
        f.write("Site, Latitude, Longitude, Altitude_kmasl, Starttime\n")
        for site, coords in config["sensor_coordinates"].items():
            f.write(
                ", ".join(
                    [
                        site,
                        str(round(coords["lat"], 3)),
                        str(round(coords["lng"], 3)),
                        str(round(coords["alt"] / 1000, 3)),
                        "2019-01-01",
                    ]
                )
                + "\n"
            )

    # Update/create yaml files for proffast (one per site)
    for sensor in config["sensors_to_consider"]:
        with open(YAML_TEMPLATE, "r") as f:
            file_content = "".join(f.readlines())

        replacements = {
            "SERIAL_NUMBER": str(config["sensor_serial_numbers"][sensor]).zfill(3),
            "SITE": sensor,
            "PROJECT_DIR": PROJECT_DIR,
            "COMMIT_SHA": subprocess.check_output(
                ["git", "rev-parse", "--short", "--verify", "HEAD"]
            )
            .decode()
            .replace("\n", ""),
        }

        for key, value in replacements.items():
            file_content = file_content.replace(f"%{key}%", value)

        with open(f"{PROJECT_DIR}/inputs/{sensor}-pylot-config.yml", "w") as f:
            f.write(file_content)
