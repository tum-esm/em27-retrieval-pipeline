import subprocess
import os
import shutil

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))

IFG_SRC_CLOUD = "/mnt/measurementData/mu"
DST_DSS = "/home/esm/em27_ifg_dss/proffast-archive"

get_dir_size = lambda d: int(
    subprocess.check_output(["du", "-d", "0", "-b", d])
    .decode()
    .replace("\t", " ")
    .split(" ")[0]
) - int(subprocess.check_output(["stat", '--printf="%s"', d]).decode().replace('"', ""))


def run(sensor: str, dates: list[str], config: dict):
    start_date = min(dates)
    end_date = max(dates)
    output_src = f"{PROJECT_DIR}/outputs/{sensor}_SN{str(config['serial_numbers'][sensor]).zfill(3)}_{start_date}_{end_date}"
    output_csv = f"{output_src}/combined_invparms_{sensor}_{start_date}-{end_date}.csv"

    # determine output directory path on DSS
    day_was_successful = os.path.isfile(output_csv)
    if day_was_successful:
        with open(output_csv, "r") as f:
            day_was_successful = len(f.readlines()) > 1
    output_dst = f"{DST_DSS}/{sensor}/proffast-outputs{'' if day_was_successful else '-failed'}/{start_date}_{end_date}"

    # move output data
    if os.path.isdir(output_dst):
        shutil.rmtree(output_dst)
    shutil.move(output_src, output_dst)

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
            if get_dir_size(ifg_src) == get_dir_size(ifg_dst):
                shutil.rmtree(ifg_src)
