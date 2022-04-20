import os
import sys
import time
from src import utils, load_config, upload_request, download_file, process_tar_file

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))


def main(DATE, CONFIG):
    all_filetypes = ["mod", "map"]
    unfinished_filetypes = [t for t in all_filetypes if CONFIG["downloadTypes"][t]]
    lat_str, lng_str = utils.format_coordinates(CONFIG["lat"], CONFIG["lng"])
    FILESCHEMA = {
        "map": {
            "type": "map",
            "cache": f"{DATE}_{lat_str}_{lng_str}.map",
            "tar": f"maps_{lat_str}{lng_str}_{DATE}_{DATE}.tar",
            "dst": f"L1{DATE}.map",
        },
        "mod": {
            "type": "mod",
            "cache": f"{DATE}_{lat_str}_{lng_str}.mod",
            "tar": f"mods_{lat_str}{lng_str}_{DATE}_{DATE}.tar",
            "dst": f"NCEP_{DATE}_{lat_str}_{lng_str}.mod",
        },
    }

    # Try to copy requested files from cache
    for FILETYPE in [*unfinished_filetypes]:
        if utils.move_output_from_cache(CONFIG["dst"], FILESCHEMA[FILETYPE]):
            utils.print_blue(DATE, FILETYPE.upper(), f"Finished from cache")
            unfinished_filetypes.remove(FILETYPE)

    # End computation if all requested files have already been cached
    if len(unfinished_filetypes) == 0:
        return

    # Write request file & upload the request file
    upload_was_successful = upload_request.run(date=DATE, config=CONFIG)
    if not upload_was_successful:
        return

    # Download and process all files (since they are
    # computed all, we might as well cache them)
    for FILETYPE in all_filetypes:
        download_successful = download_file.run(
            date=DATE, config=CONFIG, files=FILESCHEMA[FILETYPE]
        )
        if download_successful:
            processing_successful = process_tar_file.run(
                date=DATE, files=FILESCHEMA[FILETYPE]
            )

        if (not download_successful) or (not processing_successful):
            unfinished_filetypes.remove(FILETYPE)

    # Move the file to the desired output location
    for FILETYPE in unfinished_filetypes:
        if utils.move_output_from_cache(CONFIG["dst"], FILESCHEMA[FILETYPE]):
            utils.print_blue(DATE, FILETYPE, "Finished from source")
        else:
            utils.print_red(DATE, FILETYPE, "Something went wrong")


if __name__ == "__main__":
    _CONFIG = load_config.run()

    for _DATE in _CONFIG["dates"]:
        if utils.delta_days_until_now(_DATE) < _CONFIG["minimumDaysDelay"]:
            utils.print_blue(_DATE, "MAP/MOD", f"Date is too recent, skipping")
            continue
        main(_DATE, _CONFIG)
