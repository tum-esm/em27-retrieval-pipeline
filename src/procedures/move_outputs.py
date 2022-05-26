import subprocess
import os
import shutil

from numpy import str_

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))

IFG_SRC_CLOUD = "/mnt/measurementData/mu"
DST_DSS = "/home/esm/em27_ifg_dss/proffast-archive"


def _directories_are_equal(_dir1: str_, _dir2: str_):
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
    if day_was_successful:
        output_dst = f"{DST_DSS}/{sensor}/proffast-outputs/{date}"
    else:
        output_dst = f"{DST_DSS}/{sensor}/proffast-outputs-failed/{date}"

    # move output data
    if os.path.isdir(output_dst):
        shutil.rmtree(output_dst)
    shutil.move(output_src, output_dst)

    # move input data (interferograms)
    ifg_src = f"{IFG_SRC_CLOUD}/{sensor}_ifg/{date}"
    ifg_dst = f"{DST_DSS}/{sensor}/ifgs/{date}"
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
