import os
import subprocess
import time
import json
from rich.console import Console
import shutil

console = Console()
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))


def main():

    with open(f"{PROJECT_DIR}/config.json") as f:
        config = json.load(f)

    try:
        LAT = config["lat"]
        LNG = config["lng"]
        DATES = config["dates"]
        USER = config["user"]
        DST = config["dst"]
        assert os.path.isdir(DST)
    except KeyError:
        raise Exception("config.json invalid")
    except AssertionError:
        raise Exception("Destination directory does not exist")

    for DATE in DATES:
        lat_str = str(abs(round(LAT))).zfill(2) + ("N" if LAT > 0 else "S")
        lng_str = str(abs(round(LNG))).zfill(3) + ("E" if LNG > 0 else "W")
        cached_file_path = f"{PROJECT_DIR}/cache/L1_{DATE}_{lat_str}{lng_str}.map"
        dst_file_path = f"{DST}/L1{DATE}.map"

        if os.path.isfile(cached_file_path):
            shutil.copyfile(cached_file_path, dst_file_path)
            console.print(f"[bold blue]{DATE} - Map Download - Finished from cache")
            continue

        with open(f"input_file.txt", "w") as f:
            f.write(
                "\n".join(["L1", DATE, DATE, str(round(LAT)), str(round(LNG)), USER])
            )

        with console.status(
            f"[bold green]{DATE} - Map Download - Uploading map request"
        ) as status:
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
                    console.print_exception(show_locals=True)
                    # error, when calling login.sh too fast in a row
                    console.print(
                        f"[bold yellow]{DATE} - Map Download - too frequent file "
                        + "request, cooling down a minute"
                    )
                    time.sleep(60)

            os.remove("input_file.txt")

        map_file = f"maps_{lat_str}{lng_str}_{DATE}_{DATE}.tar"

        with console.status(f"[bold green]{DATE} - Downloading map file") as status:
            while True:
                subprocess.run(
                    [
                        "wget",
                        "--user",
                        "anonymous",
                        "--password",
                        USER,
                        f"ftp://ccycle.gps.caltech.edu/upload/modfiles/tar/maps/{map_file}",
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                if os.path.isfile(map_file):
                    break
                time.sleep(8)

        with console.status(
            f"[bold green]{DATE} - Map Download - Processing map file"
        ) as status:
            p = subprocess.run(
                ["tar", "-xvf", map_file],
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
            )
            if not os.path.isfile(cached_file_path):
                shutil.copyfile(f"L1{DATE}.map", cached_file_path)
            os.rename(f"L1{DATE}.map", dst_file_path)
            os.remove(map_file)

        console.print(f"[bold blue]{DATE} - Map Download - Finished")


if __name__ == "__main__":
    main()
