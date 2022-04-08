import os
import shutil

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))

SRC = "/home/esm/datalogger2zeno"
DST = f"{PROJECT_DIR}/inputs"


def run(site: str, serial_number: str, date: str):
    src_dir = f"{SRC}/{site}_{serial_number[1:]}"
    dst_dir = f"{DST}/{site}_pressure"
    assert os.path.isdir(src_dir)

    matching_files = list(
        filter(
            lambda f: f.startswith(f"20{date[:2]}-{date[2:4]}-{date[4:]}_00-00-")
            and f.endswith(".dat"),
            os.listdir(src_dir),
        )
    )

    assert len(matching_files) > 0, "No datalogger file found"
    assert len(matching_files) < 2, f"Multiple datalogger files found: {matching_files}"

    src_file = f"{src_dir}/{matching_files[0]}"
    dst_file = f"{dst_dir}/{matching_files[0]}"
    with open(src_file, "r") as f:
        line_count = len(f.readlines())
        # 1440 minutes per day + 1 header line
        assert (
            line_count == 1441
        ), f"Datalogger file is incomplete: Only {line_count} lines"

    # create/empty output directory
    dst_dir = f"{DST}/{site}_pressure"
    if os.path.isdir(dst_dir):
        shutil.rmtree(dst_dir)
    os.mkdir(dst_dir)

    # copy datalogger file
    shutil.copy(src_file, dst_file)
