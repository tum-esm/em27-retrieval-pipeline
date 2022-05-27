from datetime import datetime
import os
from src import utils


def date_string_is_valid(date_string: str):
    try:
        datetime.strptime(date_string[:8], "%Y%m%d")
        return True
    except (ValueError, IndexError, TypeError):
        return False


def unique(xs: list[str]):
    if len(xs) == 0:
        return []
    xs = list(sorted(xs))
    new_xs = [xs[0]]
    for x in xs[1:]:
        if new_xs[-1] != x:
            new_xs.append(x)
    return new_xs


PROJECT_DIR, CONFIG = utils.load_setup(validate=True)
DST = f"{PROJECT_DIR}/retrival-state-report.csv"
IFG_SRC = CONFIG["src"]["interferograms"]
SENSORS = CONFIG["sensorsToConsider"]


rows = [["date"] + SENSORS]
dates = []

for s in SENSORS:
    dates += os.listdir(f'{CONFIG["src"]["interferograms"]}/{s}_ifg')

dates = list(
    sorted(
        unique(list(map(lambda x: x[:8], list(filter(date_string_is_valid, dates)))))
    )
)

for date in dates:
    rows.append(
        [
            date,
            *[
                "X" if os.path.isdir(f"{IFG_SRC}/{s}_ifg/{date}") else "-"
                for s in SENSORS
            ],
        ]
    )

with open(DST, "w") as f:
    f.write("\n".join([", ".join(r) for r in rows]))
