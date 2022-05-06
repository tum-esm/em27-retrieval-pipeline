import os
import subprocess
from src import load_config, utils

CONFIG = load_config.run()

        
def run(start_date: str, end_date: str):
    for filetype in ["map", "mod"]:
        tar_filename = None
        
        for filename in utils.get_possible_tar_filenames(filetype, start_date, end_date):
            if os.path.isfile(filename):
                tar_filename = filename
                break
        
        # skip if download not successful
        if tar_filename == None:
            return
        
        subprocess.run(
            ["tar", "-xvf", tar_filename],
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
        os.remove(tar_filename)

        # store generated file in internal cache
        for date_string in utils.get_date_list_from_range_query(start_date, end_date):
            cache_filename = CONFIG["sharedCachePath"] + "/" + utils.get_cache_filename(filetype, date_string)
            dst_filename = utils.get_dst_filename(filetype, date_string)
            if os.path.isfile(cache_filename):
                os.remove(cache_filename)
            os.rename(dst_filename, cache_filename)
