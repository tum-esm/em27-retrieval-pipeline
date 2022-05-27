import json
import shutil
from src import download_profiles as dp
from src import Query


class QueryProcess:

    def __init__(self, query: Query):
        self.results = {
            "successful": [],
            "skipped": [],
            "failed": [],
        }
        self.query = query
        self.process()


    def _start(self):
        date_list = dp.utils.get_date_list_from_range_query(self.start_date, self.end_date)
        config = self.config
        
        if not dp.utils.query_is_present_in_cache(self.query):
            dp.upload_request.run(self.query)
            dp.download_file.run(self.query)
            dp.process_tar_file.run(self.query)

        # Move the file to the desired output location
        for date_string in date_list:
            try:
                for filetype in ["mod", "map"]:
                    shutil.copyfile(
                        config["sharedCachePath"]
                        + "/"
                        + dp.utils.get_cache_filename(filetype, date_string, config),
                        config["dst"] + "/" + dp.utils.get_dst_filename(filetype, date_string, config),
                    )
                self.results["successful"].append(date_string)
            except FileNotFoundError:
                if dp.utils.delta_days_until_now(date_string) < 5:
                    self.results["skipped"].append(date_string)
                else:
                    self.results["failed"].append(date_string)


    def main(query):
        config = dp.load_config.run(validate=True)
        
        dp.utils.print_blue(f"Processing: {query}")
        _results = process_query(*query.split("-"), config)

        dp.utils.print_blue(f"Done: {_results}")
