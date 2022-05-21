import subprocess
import os
import shutil

from numpy import str_

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))

IFG_SRC_CLOUD = "/mnt/measurementData/mu"
DST_DSS = "/home/esm/em27_ifg_dss/proffast-archive"


def directories_are_equal(_dir1: str_, _dir2: str_):
    return len(
        subprocess.run(
            ["diff", "--brief", "--recursive", _dir1, _dir2 ],
            capture_output=True
        ).stdout.decode().split("\n")
    ) == 1


def run(sensor: str, dates: list[str], config: dict):
    start_date = min(dates)
    end_date = max(dates)
    output_src = f"{PROJECT_DIR}/outputs/{sensor}_SN{str(config['serial_numbers'][sensor]).zfill(3)}_{start_date}_{end_date}"
    output_csv = f"{output_src}/combined_invparms_{sensor}_{start_date}-{end_date}.csv"

    if not os.path.isdir(output_src):
        return "failed"

    # determine output directory path on DSS
    day_was_successful = os.path.isfile(output_csv)
    if day_was_successful:
        with open(output_csv, "r") as f:
            day_was_successful = len(f.readlines()) > 1
    output_dst = (
        f"{DST_DSS}/{sensor}/proffast-outputs"
        + f"{'' if day_was_successful else '-failed'}/{start_date}_{end_date}"
    )

    # move output data
    if os.path.isdir(output_dst):
        shutil.rmtree(output_dst)
    shutil.move(output_src, output_dst)

    message = []

    # move input data (interferograms)
    for date in dates:
        ifg_src = f"{IFG_SRC_CLOUD}/{sensor}_ifg/{date}"
        ifg_dst = f"{DST_DSS}/{sensor}/ifgs/{date}"

        if os.path.isdir(ifg_src):
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
            if directories_are_equal(ifg_src, ifg_dst):
                shutil.rmtree(ifg_src)
                message.append(f"{date}: ok (dst-dir: {ifg_dst})")
            else:
                message.append(f"{date}: copy not complete because directories differ")
        else:
            message.append(f"{date}: src not on cloud, skipping copy process")

    return ", ".join(message)
