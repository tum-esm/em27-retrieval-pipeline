import os
import subprocess
from src import custom_types

# TODO: Convert this into a class
# TODO: convert the output structure from "dst/sensor/ifgs/date" to
#       "dst/ifgs/sensor/date". Then it is the same everywhere


def get_existing_src_directories(
    config: custom_types.ConfigDict, sensor: str, date: str
) -> list[str]:
    src_directories = [
        os.path.join(config["src"]["interferograms"]["upload"], sensor, date),
        *[
            os.path.join(d, sensor, date)
            for d in config["src"]["interferograms"]["other"]
        ],
        os.path.join(config["dst"], sensor, "ifgs", date),
    ]
    return [x for x in src_directories if os.path.isdir(x)]


def assert_directory_equality(directory_list: list[str]) -> None:
    for a, b in zip(directory_list[:-1], directory_list[1:]):
        assert (
            len(
                subprocess.run(
                    ["diff", "--brief", "--recursive", a, b], capture_output=True
                )
                .stdout.decode()
                .split("\n")
            )
            == 1
        ), f"Directories {a} and {b} exist but differ"
