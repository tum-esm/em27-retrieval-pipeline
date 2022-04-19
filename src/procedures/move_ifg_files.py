import os
import shutil

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))

SRC_CLOUD = "/mnt/measurementData/mu"
SRC_DSS = "/home/esm/em27_ifg_dss/em27_ifg_dss"
DST = f"{PROJECT_DIR}/inputs"


def run(site: str, date: str):
    src_date_path = f"{SRC_CLOUD}/{site}_ifg/20{date}"
    if not os.path.isdir(src_date_path):
        src_date_path = f"{SRC_DSS}/{site}_ifg/20{date}"
    assert os.path.isdir(src_date_path)

    # Create empty output directory for that date
    dst_date_path = f"{DST}/{site}/ifg/{date}"
    if os.path.isdir(dst_date_path):
        shutil.rmtree(dst_date_path)
    os.mkdir(dst_date_path)

    # move all valid ifg files and rename them properly
    for ifg_file in os.listdir(src_date_path):
        old_path = f"{src_date_path}/{ifg_file}"
        if os.path.isfile(old_path):
            assert len(ifg_file.split(".")) == 3
            ifg_number = ifg_file.split(".")[-1]
            assert ifg_number.isnumeric()
            shutil.copy(old_path, f"{dst_date_path}/{date}SN.{ifg_number}")
