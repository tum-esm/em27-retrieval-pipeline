from datetime import datetime, timedelta
from rich.console import Console
import os
from src import load_config

console = Console()
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


def get_possible_tar_filenames(filetype: str, start_date: str, end_date: str):
    # if I request 200-300 on day 302 the resulting tar file might be named "200-300"
    # or "200-299" or "200-298" ... depending on the delay of the server
    date_with_min_delay = min(end_date, (datetime.now() - timedelta(days=1)).strftime("%Y%m%d"))
    date_with_max_delay = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")
    if end_date <= date_with_max_delay:
        possible_end_dates = [end_date]
    else:
        possible_end_dates = get_date_list_from_range_query(
            date_with_max_delay,
            date_with_min_delay
        )
    return [
        get_tar_filename(filetype, start_date, possible_end_date)
        for possible_end_date in possible_end_dates
    ]


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
            CONFIG["sharedCachePath"] + "/" +
            get_cache_filename(filetype, date_string)
        ) for filetype in ["map", "mod"]
    ])
    