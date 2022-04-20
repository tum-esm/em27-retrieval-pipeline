from datetime import datetime
import os
import shutil
from rich.console import Console

console = Console()
dir = os.path.dirname
PROJECT_DIR = dir(dir(os.path.abspath(__file__)))

print_red = lambda date, filetype, message: console.print(
    f"[bold red]{date} - {filetype.upper()} Download - {message}"
)
print_blue = lambda date, filetype, message: console.print(
    f"[bold blue]{date} - {filetype.upper()} Download - {message}"
)


def delta_days_until_now(date_string):
    year, month, day = (
        int(str(date_string)[:4]),
        int(str(date_string)[4:6]),
        int(str(date_string)[6:]),
    )
    return (datetime.now() - datetime(year, month, day)).days


def format_coordinates(lat, lng):
    lat_str = str(abs(round(lat))).zfill(2) + ("N" if lat > 0 else "S")
    lng_str = str(abs(round(lng))).zfill(3) + ("E" if lng > 0 else "W")
    return lat_str, lng_str


def move_output_from_cache(dst, filenames):
    file_in_cache = f"{PROJECT_DIR}/cache/{filenames['cache']}"
    file_in_dst = f"{dst}/{filenames['dst']}"
    if os.path.isfile(file_in_cache):
        shutil.copyfile(file_in_cache, file_in_dst)
        return True
    return False
