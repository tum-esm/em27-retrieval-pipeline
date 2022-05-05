import os
import shutil
from src import utils, load_config, upload_request, download_file, process_tar_file

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG = load_config.run(validate=True)

result = {
    "successful": [],
    "skipped": [],
    "failed": [],
}

def main(start_date: str, end_date: str):
    requested_filetypes = [t for t in ("mod", "map") if CONFIG["downloadTypes"][t]]
    date_list = utils.get_date_list_from_range_query(start_date, end_date)
    
    # Download date if not found in cache
    if not all(map(utils.date_is_present_in_cache, date_list)):
        upload_request.run(start_date=date_string, end_date=date_string)
        download_file.run(start_date=date_string, end_date=date_string)
        process_tar_file.run(start_date=date_string, end_date=date_string)
    
    # Move the file to the desired output location
    for date_string in date_list:
        try:
            for filetype in requested_filetypes:
                shutil.copyfile(
                    f"{PROJECT_DIR}/cache/" + utils.get_cache_filename(filetype, date_string),
                    CONFIG["dst"] + "/" + utils.get_dst_filename(filetype, date_string)
                )
                result["successful"].append(date_string)
        except FileNotFoundError:
            if utils.delta_days_until_now(date_string) < CONFIG["minimumDaysDelay"]:
                result["skipped"].append(date_string)
            else:
                result["failed"].append(date_string)


if __name__ == "__main__":
    for query in CONFIG["dates"]:
        if utils.date_string_is_valid(query):
            utils.print_blue(f"Processing: {query}")
            main(query, query)
        elif utils.range_query_is_valid(query):
            utils.print_blue(f"Processing: {query}")
            main(*query.split("-"))
        else:
            utils.print_red(f"Query invalid: {query}")
    utils.print_blue(f"Done: {result}")
