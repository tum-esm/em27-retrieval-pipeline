import os
import subprocess
from src.utils import FileUtils, load_setup

PROJECT_DIR, CONFIG = load_setup(validate=False)

def run(query):
    for filetype in ["map", "mod"]:
        tar_filename = None

        for filename in FileUtils.get_possible_tar_filenames(filetype, query):
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
        for date_string in query.date_string_list:
            unpacked_filename = FileUtils.get_unpacked_filename(filetype, date_string, query)
            cache_filepath = (
                f"{PROJECT_DIR}/cache/"
                + FileUtils.get_cache_file_slug(date_string, query) + f".{filetype}"
            )
            if os.path.isfile(unpacked_filename):
                if os.path.isfile(cache_filepath):
                    os.remove(cache_filepath)
                os.rename(unpacked_filename, cache_filepath)
