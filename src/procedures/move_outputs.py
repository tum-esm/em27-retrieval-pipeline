import subprocess
import os
import shutil
from src import utils

PROJECT_DIR, CONFIG = utils.load_setup()

IFG_SRC = CONFIG["src"]["interferograms"]
DST = CONFIG["dst"]


def _directories_are_equal(_dir1: str, _dir2: str):
    return (
        len(
            subprocess.run(
                ["diff", "--brief", "--recursive", _dir1, _dir2], capture_output=True
            )
            .stdout.decode()
            .split("\n")
        )
        == 1
    )


def run(session):
    sensor = session["sensor"]
    date = str(session["date"])

    output_src = (
        f"{PROJECT_DIR}/outputs/{sensor}_"
        + f"SN{str(session['serial_number']).zfill(3)}_{date}_{date}"
    )
    output_csv = f"{output_src}/combined_invparms_{sensor}_{date}-{date}.csv"

    assert os.path.isdir(output_src), "output directory missing"

    # determine output directory path on DSS
    day_was_successful = os.path.isfile(output_csv)
    if day_was_successful:
        with open(output_csv, "r") as f:
            day_was_successful = len(f.readlines()) > 1

    output_dst_success = f"{DST}/{sensor}/proffast-outputs/{date}"
    output_dst_failed = f"{DST}/{sensor}/proffast-outputs-failed/{date}"

    # remove old outputs
    if os.path.isdir(output_dst_success):
        shutil.rmtree(output_dst_success)
    if os.path.isdir(output_dst_failed):
        shutil.rmtree(output_dst_failed)

    # move the output data
    output_dst = output_dst_success if day_was_successful else output_dst_failed
    shutil.move(output_src, output_dst)

    # move input data (interferograms)
    ifg_src = f"{IFG_SRC}/{sensor}_ifg/{date}"
    ifg_dst = f"{DST}/{sensor}/ifgs/{date}"
    assert os.path.isdir(ifg_src), "src not on cloud, skipping copy process"

    # Create empty output directory for that date. Do not
    # delete overwrite data automatically, add duplicate
    # folders named "_1", "_2", ... instead
    if os.path.isdir(ifg_dst):
        ifg_dst += "_1"
    while os.path.isdir(ifg_dst):
        ifg_dst = "_".join(
            [*ifg_dst.split("_")[:-1], str(int(ifg_dst.split("_")[-1]) + 1)]
        )

    # move the whole directory
    shutil.copytree(ifg_src, ifg_dst)

    # Only remove input src if copy was successful
    assert _directories_are_equal(
        ifg_src, ifg_dst
    ), "directories differ, skipped removal"

    shutil.rmtree(ifg_src)
