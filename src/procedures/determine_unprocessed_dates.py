import os
from datetime import datetime

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))

IFG_UPLOAD_DIR = f"/mnt/measurementData/mu"
START_DATE = "20210101"


def is_valid_date(s):
    try:
        datetime.strptime(s, "%Y%m%d")
        return s >= START_DATE
    except ValueError:
        return False


def take(xs, n):
    if len(xs) < n:
        return n
    else:
        return xs


def run(config: dict):
    next_dates = []
    for sensor in config["sensors_to_consider"]:

        # Renaming all folders YYYYMMDD_XX to YYYYMMDD
        for d in os.listdir(f"{IFG_UPLOAD_DIR}/{sensor}_ifg"):
            if (
                os.path.isdir(f"{IFG_UPLOAD_DIR}/{sensor}_ifg/{d}")
                and is_valid_date(d[:8])
                and len(d) == 11
                and d[8] == "_"
            ):
                os.rename(
                    f"{IFG_UPLOAD_DIR}/{sensor}_ifg/{d}",
                    f"{IFG_UPLOAD_DIR}/{sensor}_ifg/{d[:8]}",
                )

        next_dates.append(
            {
                "sensor": sensor,
                "dates": [
                    d
                    for d in os.listdir(f"{IFG_UPLOAD_DIR}/{sensor}_ifg")
                    if is_valid_date(d)
                ],
            }
        )
    sorted_next_dates = []
    for x in next_dates:
        sorted_next_dates.append(
            {"sensor": x["sensor"], "dates": list(sorted(x["dates"]))}
        )
    return sorted_next_dates
