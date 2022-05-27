
from datetime import datetime, timedelta
import os
from src.utils import load_setup

PROJECT_DIR, CONFIG = load_setup(validate=False)

class FileUtils:

    @staticmethod
    def _format_coordinates(query):
        lat_str = str(abs(round(query.lat))).zfill(2) + ("N" if query.lat > 0 else "S")
        lon_str = str(abs(round(query.lon))).zfill(3) + ("E" if query.lon > 0 else "W")
        return lat_str, lon_str

    @staticmethod
    def get_cache_file_slug(date_string: str, query):
        lat_str, lon_str = FileUtils._format_coordinates(query)
        return f"{date_string}_{lat_str}_{lon_str}"

    @staticmethod
    def get_dst_file_slug(date_string: str, query):
        return f"{query.sensor}{date_string}"
    
    @staticmethod
    def get_unpacked_filename(filetype: str, date_string: str, query):
        lat_str, lon_str = FileUtils._format_coordinates(query)
        return {
            "map": f"{query.sensor}{date_string}.map",
            "mod": f"NCEP_{date_string}_{lat_str}_{lon_str}.mod",
        }[filetype]
    
    @staticmethod
    def get_possible_tar_filenames(filetype: str, query):
        # if I request 200-300 on day 302 the resulting tar file might be named "200-300"
        # or "200-299" or "200-298" ... depending on the delay of the server
        date_with_max_delay = max(
            datetime.strftime(datetime.utcnow() - timedelta(days=10), "%Y%m%d"),
            query.t_from_str
        )
        possible_end_dates = list(filter(
            lambda d: (d == query.t_to_str) or (d >= date_with_max_delay),
            query.date_string_list
        ))
        
        lat_str, lon_str = FileUtils._format_coordinates(query)
        return [
            f"{filetype}s_{lat_str}{lon_str}_{query.t_from_str}_{d}.tar"
            for d in possible_end_dates
        ]

    @staticmethod
    def query_is_present_in_cache(query):
        q = query.clone()
        is_present = True
        while (q.t_from_str <= query.t_to_str) and is_present:
            file_slug = FileUtils.get_cache_file_slug(q.t_from_str, query)
            is_present &= os.path.isfile(f"{PROJECT_DIR}/cache/{file_slug}.map")
            is_present &= os.path.isfile(f"{PROJECT_DIR}/cache/{file_slug}.mod")
            q.t_from_datetime += timedelta(days=1)
        del q
        return is_present

    @staticmethod
    def t_exists_in_dst(date_string: str, query):
        d = f'{CONFIG["dst"]}/{query.sensor}{query.serial_number}/'
        dst_slug = FileUtils.get_dst_file_slug(date_string, query)
        return (
            os.path.isfile(f"{d}/{dst_slug}.map")
            and
            os.path.isfile(f"{d}/{dst_slug}.mod")
        )
    