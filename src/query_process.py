import os
import shutil
from src import Query, download_steps
from src.utils import FileUtils, load_setup

PROJECT_DIR, CONFIG = load_setup(validate=False)


class QueryProcess:
    """
    This class processes one query.

    If not all query dates are present in the cache yet:
    1. Upload the request to ccycle.ftp.caltech.edu
    2. Download generated tar-file
    3. Extract profiles from tar-file and save them in the cache

    Finally it copies all request profiles from cache to the dst directy.
    """
    
    def __init__(self, query: Query):
        self.failed_dates = []
        self.query = query
        self._start()
        if len(self.failed_dates) > 0:
            print(f'failed days: {self.failed_dates}')

    def _start(self):
        if not FileUtils.query_is_present_in_cache(self.query):
            download_steps.upload_request.run(self.query)
            download_steps.download_file.run(self.query)
            download_steps.process_tar_file.run(self.query)

        # Move the files to the desired output location
        for date_string in self.query.date_string_list:
            try:
                cache_file_slug = FileUtils.get_cache_file_slug(date_string, self.query)
                dst_file_slug = FileUtils.get_dst_file_slug(date_string, self.query)
                dst_dir = f'{CONFIG["dst"]}/{self.query.sensor}{self.query.serial_number}'
                if not os.path.isdir(dst_dir):
                    os.mkdir(dst_dir)
                for filetype in ["mod", "map"]:
                    shutil.copyfile(
                        f"{PROJECT_DIR}/cache/{cache_file_slug}.{filetype}",
                        f'{dst_dir}/{dst_file_slug}.{filetype}',
                    )
            except FileNotFoundError:
                self.failed_dates.append(date_string)
