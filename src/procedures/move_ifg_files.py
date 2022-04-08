import os
import shutil

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))

SRC = "/mnt/measurementData/mu"
DST = f"{PROJECT_DIR}/inputs"


def run(site: str, date: str):
    src_date_path = f"{SRC}/{site}_ifg/20{date}"
    assert os.path.isdir(src_date_path)

    # create/empty output directory
    dst_site_path = f"{DST}/{site}_ifg"
    dst_date_path = f"{dst_site_path}/{date}"
    if os.path.isdir(dst_site_path):
        shutil.rmtree(dst_site_path)
    os.mkdir(dst_site_path)
    os.mkdir(dst_date_path)

    # move all valid ifg files and rename them properly
    for ifg_file in os.listdir(src_date_path):
        old_path = f"{src_date_path}/{ifg_file}"
        if os.path.isfile(old_path):
            assert len(ifg_file.split(".")) == 3
            ifg_number = ifg_file.split(".")[-1]
            assert ifg_number.isnumeric()
            shutil.copy(old_path, f"{dst_date_path}/{date}SN.{ifg_number}")
