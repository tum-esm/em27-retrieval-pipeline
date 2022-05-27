import os
import subprocess
from src import download_profiles


def run(start_date: str, end_date: str, config: dict):
    for filetype in ["map", "mod"]:
        tar_filename = None

        for filename in download_profiles.utils.get_possible_tar_filenames(
            filetype, start_date, end_date, config
        ):
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
        for date_string in download_profiles.utils.get_date_list_from_range_query(start_date, end_date):
            cache_filename = (
                config["sharedCachePath"]
                + "/"
                + download_profiles.utils.get_cache_filename(filetype, date_string, config)
            )
            dst_filename = download_profiles.utils.get_unpacked_filename(filetype, date_string, config)
            if os.path.isfile(dst_filename):
                if os.path.isfile(cache_filename):
                    os.remove(cache_filename)
                os.rename(dst_filename, cache_filename)
