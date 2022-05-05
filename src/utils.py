from datetime import datetime
import os
from rich.console import Console
from src import load_config

console = Console()
dir = os.path.dirname
PROJECT_DIR = dir(dir(os.path.abspath(__file__)))
CONFIG = load_config.run()

print_red = lambda message: console.print(f"[bold red]{message}")
print_blue = lambda message: console.print(f"[bold blue]{message}")

def date_string_is_valid(date_string: str):
    try:
        datetime.strptime(date_string, "%Y%m%d")
        return True
    except ValueError:
        return False

def range_query_is_valid(range_query: str):
    try:
        assert len(range_query) == 17
        assert range_query[8] == "-"
        assert len(range_query.split("-")) == 2
        start_date, end_date = range_query.split("-")
        assert date_string_is_valid(start_date)
        assert date_string_is_valid(end_date)
        return True
    except ValueError:
        return False

def delta_days_until_now(date_string: str):
    return (datetime.now() - datetime.strptime(date_string, "%Y%m%d")).days

def get_date_list_from_range_query(start_date: str, end_date: str):    
    date_list = []
    for date_string in range(int(start_date), int(end_date) + 1):
        if date_string_is_valid(str(date_string)):
            date_list.append(str(date_string))
    return date_list

def _format_coordinates(lat, lng):
    lat_str = str(abs(round(lat))).zfill(2) + ("N" if lat > 0 else "S")
    lng_str = str(abs(round(lng))).zfill(3) + ("E" if lng > 0 else "W")
    return lat_str, lng_str

# TODO: Return a list of possible tar filenames (the last 6-7 days)
def get_tar_filename(filetype: str, start_date: str, end_date: str):
    lat_str, lng_str = _format_coordinates(CONFIG["lat"], CONFIG["lng"])
    return f"{filetype}s_{lat_str}{lng_str}_{start_date}_{end_date}.tar"

def get_cache_filename(filetype: str, date_string: str):
    lat_str, lng_str = _format_coordinates(CONFIG["lat"], CONFIG["lng"])
    return f"{date_string}_{lat_str}_{lng_str}.{filetype}"

def get_dst_filename(filetype: str, date_string: str):
    lat_str, lng_str = _format_coordinates(CONFIG["lat"], CONFIG["lng"])
    return {
        "map": f"{CONFIG['stationId']}{date_string}.map",
        "mod": f"NCEP_{date_string}_{lat_str}_{lng_str}.mod",
    }[filetype]

def date_is_present_in_cache(date_string: str):
    return all([
        os.path.isfile(
            f"{PROJECT_DIR}/cache/" +
            get_cache_filename(filetype, date_string)
        ) for filetype in ["map", "mod"]
    ])