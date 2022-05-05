import os
import subprocess
from src import utils

dir = os.path.dirname
PROJECT_DIR = dir(dir(os.path.abspath(__file__)))

        
def run(start_date: str, end_date: str):
    for filetype in ["map", "mod"]:
        tar_filename = utils.get_tar_filename(filetype, start_date, end_date)
        
        # skip if download not successful
        if not os.path.isfile(tar_filename):
            return
        
        subprocess.run(
            ["tar", "-xvf", tar_filename],
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
        os.remove(tar_filename)

        # store generated file in internal cache
        for date_string in utils.get_date_list_from_range_query(f"{start_date}-{end_date}"):
            cache_filename = f"{PROJECT_DIR}/cache/" + utils.get_cache_filename(filetype, date_string)
            dst_filename = utils.get_dst_filename(filetype, date_string)
            if os.path.isfile(cache_filename):
                os.remove(cache_filename)
            os.rename(dst_filename, cache_filename)
