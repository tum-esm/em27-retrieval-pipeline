import os
import shutil


dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))


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

    assert os.path.isfile(
        f"{PROJECT_DIR}/proffastpylot/prf/invers20"
    ) and os.path.isfile(
        f"{PROJECT_DIR}/proffastpylot/prf/pcxs20"
    ), "PROFFAST not compiled completely"

    # clear directory "inputs" and "outputs"
    for d in ["inputs", "outputs"]:
        for f in os.listdir(f"{PROJECT_DIR}/{d}"):
            filepath = f"{PROJECT_DIR}/{d}/{f}"
            if os.path.isdir(filepath):
                shutil.rmtree(filepath)
            else:
                if not filepath.endswith(".gitkeep"):
                    os.remove(filepath)

    # Create 'coords.csv' file
    with open(f"{PROJECT_DIR}/inputs/coords.csv", "w") as f:
        f.write("Site,\tLatitude,\tLongitude,\tAltitude_kmasl,\tStarttime\n")
        for site, coords in config["sensor_coordinates"].items():
            f.write(
                ",\t\t".join(
                    [
                        site,
                        str(round(coords["lat"], 3)),
                        str(round(coords["lng"], 3)),
                        str(round(coords["alt"] / 1000, 3)),
                        "\t2019-01-01",
                    ]
                )
                + "\n"
            )
