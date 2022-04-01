from datetime import datetime
import os
import subprocess
import sys
import time
import json
from rich.console import Console
import shutil

console = Console()
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
MINIMUM_DELAY_DAYS = 5
UPLOAD_RETRIES = 1
TIMEOUT = 300  # abort download after 5 minutes


def date_is_to_recent(date_string):
    year, month, day = (
        int(str(date_string)[:4]),
        int(str(date_string)[4:6]),
        int(str(date_string)[6:]),
    )
    delta_to_now = datetime.now() - datetime(year, month, day)
    return delta_to_now.days < MINIMUM_DELAY_DAYS


def format_coordinates(lat, lng):
    lat_str = str(abs(round(lat))).zfill(2) + ("N" if lat > 0 else "S")
    lng_str = str(abs(round(lng))).zfill(3) + ("E" if lng > 0 else "W")
    return lat_str, lng_str


def upload_request(date, user):
    with console.status(
        f"[bold blue]{date} - Map/Mod Download - Uploading request",
        spinner_style="bold blue",
    ):
        upload_attempts = 0
        while True:
            upload_attempts += 1
            try:
                result = subprocess.run(
                    ["bash", f"{PROJECT_DIR}/upload_request.sh"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env={**os.environ.copy(), "PASSWD": user},
                )
                assert result.returncode == 0
                break
            except:
                if "Access failed: 553" in result.stderr.decode():
                    if upload_attempts >= (UPLOAD_RETRIES + 1):
                        console.print(
                            f"[bold blue]{date} - MAP/MOD Download - "
                            + "Missing data, skipping this date"
                        )
                        return False

                    console.print(
                        f"[bold blue]{date} - MAP/MOD Download - "
                        + "Rate limiting or missing data, retrying once in 1 minute"
                    )
                    time.sleep(60)
                else:
                    console.print(
                        f"[bold red]{date} - MAP/MOD Download - "
                        + f"Uploading request failed: {result.stderr.decode()}"
                    )
                    return

        return True


def download_file(date, user, filenames, filetype):
    with console.status(
        f"[bold blue]{date} - {filetype.upper()} Download - Downloading file",
        spinner_style="bold blue",
    ):
        running_time = 0
        while True:
            result = subprocess.run(
                [
                    "wget",
                    "--user",
                    "anonymous",
                    "--password",
                    user,
                    f"ftp://ccycle.gps.caltech.edu/upload/modfiles/tar/{filetype}s/{filenames[filetype]['tar']}",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            if os.path.isfile(filenames[filetype]["tar"]):
                break
            else:
                if ".tar ... \nNo such file" not in result.stderr.decode():
                    console.print(
                        f"[bold red]{date} - {filetype.upper()} Download - "
                        + f"command 'wget ...' returned "
                        + f"a non-zero exit code: {result.stderr.decode()}"
                    )
                    sys.exit()
                if running_time > TIMEOUT:
                    console.print(
                        f"[bold yellow]{date} - {filetype.upper()} Download - Timed out after 5 minutes"
                    )
                    sys.exit()
                running_time += 8
                time.sleep(8)


def process_tar_file(date, filenames, filetype):
    with console.status(
        f"[bold blue]{date} - {filetype.upper()} Download - Processing file",
        spinner_style="bold blue",
    ):
        filepath_cache = f"{PROJECT_DIR}/cache/{filenames[filetype]['cache']}"
        filepath_tar = filenames[filetype]["tar"]
        filepath_dst = filenames[filetype]["dst"]

        result = subprocess.run(
            ["tar", "-xvf", filepath_tar],
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
        if result.returncode != 0:
            console.print(
                f"[bold red]{date} - {filetype.upper()} Download - "
                + f"command 'tar ...' returned "
                + f"a non-zero exit code: {result.stderr.decode()}"
            )
            sys.exit()
        assert os.path.isfile(filepath_dst)

        # remove previously cached file
        if os.path.isfile(filepath_cache):
            os.remove(filepath_cache)

        # store generated file in internal cache
        os.rename(filepath_dst, filepath_cache)
        os.remove(filepath_tar)


def move_output_from_cache(dst, filenames, filetype):
    file_in_cache = f"{PROJECT_DIR}/cache/{filenames[filetype]['cache']}"
    file_in_dst = f"{dst}/{filenames[filetype]['dst']}"
    if os.path.isfile(file_in_cache):
        shutil.copyfile(file_in_cache, file_in_dst)
        return True
    return False


def main():

    with open(f"{PROJECT_DIR}/config.json") as f:
        config = json.load(f)

    try:
        LAT = config["lat"]
        LNG = config["lng"]
        DATES = config["dates"]
        USER = config["user"]
        DST = config["dst"]
        DOWNLOAD_MAP = config["downloadMap"]
        DOWNLOAD_MOD = config["downloadMod"]
        assert os.path.isdir(DST)
    except KeyError:
        raise Exception("config.json invalid")
    except AssertionError:
        raise Exception("Destination directory does not exist")

    for DATE in DATES:
        if date_is_to_recent(DATE):
            console.print(
                f"[bold blue]{DATE} - Map/Mod Download - "
                + f"Date is too recent, data available with {MINIMUM_DELAY_DAYS} days delay"
            )
            continue

        lat_str, lng_str = format_coordinates(LAT, LNG)

        filenames = {
            "map": {
                "cache": f"{DATE}_{lat_str}_{lng_str}.map",
                "tar": f"maps_{lat_str}{lng_str}_{DATE}_{DATE}.tar",
                "dst": f"L1{DATE}.map",
            },
            "mod": {
                "cache": f"{DATE}_{lat_str}_{lng_str}.mod",
                "tar": f"mods_{lat_str}{lng_str}_{DATE}_{DATE}.tar",
                "dst": f"NCEP_{DATE}_{lat_str}_{lng_str}.mod",
            },
        }

        all_filetypes = ["map", "mod"]
        unfinished_filetypes = []
        if DOWNLOAD_MAP:
            unfinished_filetypes.append("map")
        if DOWNLOAD_MOD:
            unfinished_filetypes.append("mod")

        # Try to copy requested files from cache
        for filetype in [*unfinished_filetypes]:
            file_move_successful = move_output_from_cache(DST, filenames, filetype)
            if file_move_successful:
                console.print(
                    f"[bold green]{DATE} - {filetype.upper()} Download - Finished from cache"
                )
                unfinished_filetypes.remove(filetype)

        # End computation if all requested files have already been cached
        if len(unfinished_filetypes) == 0:
            continue

        # Write request file
        with open(f"input_file.txt", "w") as f:
            f.writelines(["L1", DATE, DATE, str(round(LAT)), str(round(LNG)), USER])

        # Upload the request file
        upload_was_successful = upload_request(DATE, USER)
        os.remove("input_file.txt")
        if not upload_was_successful:
            # Skip this date if request upload failed
            continue

        # Download and process all files (since they are
        # computed all, we might as well cache them)
        for filetype in all_filetypes:
            download_file(DATE, USER, filenames, filetype)
            process_tar_file(DATE, filenames, filetype)

        # Move the file to the desired output location
        for filetype in unfinished_filetypes:
            file_move_successful = move_output_from_cache(DST, filenames, filetype)
            if file_move_successful:
                console.print(
                    f"[bold green]{DATE} - {filetype.upper()} Download - Finished from source"
                )
            else:
                console.print(
                    f"[bold red]{DATE} - {filetype.upper()} Download - Something went wrong"
                )
                sys.exit()


if __name__ == "__main__":
    main()
