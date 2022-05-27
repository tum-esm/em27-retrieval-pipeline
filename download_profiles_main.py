import json
import shutil
from src import download_profiles as dp

results = {
    "successful": [],
    "skipped": [],
    "failed": [],
}


def process_query(start_date: str, end_date: str, config: dict):
    _results = json.loads(json.dumps(results))
    
    requested_filetypes = [t for t in ("mod", "map") if config["downloadTypes"][t]]
    date_list = dp.utils.get_date_list_from_range_query(start_date, end_date)

    if dp.utils.delta_days_until_now(start_date) >= 5:
        # Download date if not found in cache
        if not all(map(lambda x: dp.utils.date_is_present_in_cache(x, config), date_list)):
            dp.upload_request.run(start_date, end_date, config)
            dp.download_file.run(start_date, end_date, config)
            dp.process_tar_file.run(start_date, end_date, config)

    # Move the file to the desired output location
    for date_string in date_list:
        try:
            for filetype in requested_filetypes:
                shutil.copyfile(
                    config["sharedCachePath"]
                    + "/"
                    + dp.utils.get_cache_filename(filetype, date_string, config),
                    config["dst"] + "/" + dp.utils.get_dst_filename(filetype, date_string, config),
                )
            _results["successful"].append(date_string)
        except FileNotFoundError:
            if dp.utils.delta_days_until_now(date_string) < 5:
                _results["skipped"].append(date_string)
            else:
                _results["failed"].append(date_string)
    
    return _results


def main():
    config = dp.load_config.run(validate=True)

    for query in config["dates"]:
        if dp.utils.date_string_is_valid(query):
            dp.utils.print_blue(f"Processing: {query}")
            _results = process_query(query, query, config)
        elif dp.utils.range_query_is_valid(query):
            dp.utils.print_blue(f"Processing: {query}")
            _results = process_query(*query.split("-"), config)
        else:
            dp.utils.print_red(f"Query invalid: {query}")

    dp.utils.print_blue(f"Done: {_results}")


if __name__ == "__main__":
    main()
