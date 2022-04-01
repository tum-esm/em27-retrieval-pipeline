from datetime import datetime
import os
import subprocess
import time
import json
from rich.console import Console
import shutil

console = Console()
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
MINIMUM_DELAY_DAYS = 5
UPLOAD_RETRIES = 1
TIMEOUT = 300  # abort download after 5 minutes


def data_should_be_available(date_string):
    year, month, day = (
        int(str(date_string)[:4]),
        int(str(date_string)[4:6]),
        int(str(date_string)[6:]),
    )
    delta_to_now = datetime.now() - datetime(year, month, day)
    return delta_to_now.days > MINIMUM_DELAY_DAYS


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
        if not data_should_be_available(DATE):
            console.print(
                f"[bold blue]{DATE} - Map/Mod Download - "
                + f"Date is too recent, please try with a {MINIMUM_DELAY_DAYS} days delay"
            )
            continue
        lat_str = str(abs(round(LAT))).zfill(2) + ("N" if LAT > 0 else "S")
        lng_str = str(abs(round(LNG))).zfill(3) + ("E" if LNG > 0 else "W")

        finished_files = {"map": False, "mod": False}
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
        filetypes = []
        if DOWNLOAD_MAP:
            filetypes.append("map")
        if DOWNLOAD_MOD:
            filetypes.append("mod")

        for filetype in filetypes:
            file_in_cache = f"{PROJECT_DIR}/cache/{filenames[filetype]['cache']}"
            file_in_dst = f"{DST}/{filenames[filetype]['dst']}"
            if os.path.isfile(file_in_cache):
                shutil.copyfile(
                    file_in_cache,
                    file_in_dst,
                )
                console.print(
                    f"[bold green]{DATE} - {filetype.upper()} Download - Finished from cache"
                )
                finished_files[filetype] = True

        if not all([finished_files[k] for k in filetypes]):
            with open(f"input_file.txt", "w") as f:
                f.write(
                    "\n".join(
                        ["L1", DATE, DATE, str(round(LAT)), str(round(LNG)), USER]
                    )
                )

            with console.status(
                f"[bold blue]{DATE} - Map/Mod Download - Uploading request",
                spinner_style="bold blue",
            ):
                upload_attempts = 0
                while True:
                    try:
                        result = subprocess.run(
                            ["bash", f"{PROJECT_DIR}/upload_request.sh"],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            env={**os.environ.copy(), "PASSWD": USER},
                        )
                        assert result.returncode == 0
                        break
                    except:
                        if "Access failed: 553" in result.stderr.decode():
                            upload_attempts += 1
                            if upload_attempts <= UPLOAD_RETRIES:
                                console.print(
                                    f"[bold blue]{DATE} - Map/Mod Download - "
                                    + "Request was rate limited, waiting 1 minute"
                                )
                                time.sleep(60)
                            else:
                                break
                        else:
                            console.print(
                                f"[bold red]{DATE} - Map/Mod Download - "
                                + f"Uploading request failed: {result.stderr.decode()}"
                            )
                            return

                if upload_attempts > UPLOAD_RETRIES:
                    console.print(
                        f"[bold red]{DATE} - Map/Mod Download - "
                        + f"Uploading request failed {UPLOAD_RETRIES + 1} times"
                    )
                    continue

                os.remove("input_file.txt")

            for filetype in filetypes:
                with console.status(
                    f"[bold blue]{DATE} - {filetype.upper()} Download - Downloading file",
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
                                USER,
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
                                    f"[bold red]{DATE} - {filetype.upper()} Download - "
                                    + f"command 'wget ...' returned "
                                    + f"a non-zero exit code: {result.stderr.decode()}"
                                )
                                return
                            if running_time > TIMEOUT:
                                console.print(
                                    f"[bold yellow]{DATE} - {filetype.upper()} Download - Timed out after 5 minutes"
                                )
                                return
                            running_time += 8
                            time.sleep(8)

                with console.status(
                    f"[bold blue]{DATE} - {filetype.upper()} Download - Processing file",
                    spinner_style="bold blue",
                ):
                    result = subprocess.run(
                        ["tar", "-xvf", filenames[filetype]["tar"]],
                        stderr=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                    )
                    if result.returncode != 0:
                        console.print(
                            f"[bold red]{DATE} - {filetype.upper()} Download - "
                            + f"command 'tar ...' returned "
                            + f"a non-zero exit code: {result.stderr.decode()}"
                        )
                        return
                    assert os.path.isfile(filenames[filetype]["dst"])

                    # store generated file in internal cache
                    file_in_cache = (
                        f"{PROJECT_DIR}/cache/{filenames[filetype]['cache']}"
                    )
                    if not os.path.isfile(file_in_cache):
                        shutil.copyfile(filenames[filetype]["dst"], file_in_cache)
                    os.rename(
                        filenames[filetype]["dst"],
                        f"{DST}/{filenames[filetype]['dst']}",
                    )
                    os.remove(filenames[filetype]["tar"])

                console.print(
                    f"[bold green]{DATE} - {filetype.upper()} Download - Finished from source"
                )


if __name__ == "__main__":
    main()
