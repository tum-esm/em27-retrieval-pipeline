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


def generate_report_name():
    return datetime.utcnow().strftime("retrival-state-report-%Y%m%d-%H%M-UTC.csv")


def get_cell_label(sensor: str, date: str):
    label = "    "
    if os.path.isdir(f"{IFG_SRC}/{sensor}_ifg/{date}"):
        label = str(len(os.listdir(f"{IFG_SRC}/{sensor}_ifg/{date}")))
        label = (" " * (4 - len(label))) + label
    return label


PROJECT_DIR, CONFIG = utils.load_setup(validate=True)
DST = f"{PROJECT_DIR}/retrival-state-report.csv"
IFG_SRC = CONFIG["src"]["interferograms"]
SENSORS = CONFIG["sensorsToConsider"]


rows = [["    date"] + [f"  {s}" for s in SENSORS]]
dates = []

for s in SENSORS:
    dates += os.listdir(f'{CONFIG["src"]["interferograms"]}/{s}_ifg')

dates = list(
    sorted(
        unique(list(map(lambda x: x[:8], list(filter(date_string_is_valid, dates)))))
    )
)

for date in dates:
    rows.append([date, *[get_cell_label(s, date) for s in SENSORS]])

with open(f"{PROJECT_DIR}/reports/{generate_report_name()}", "w") as f:
    f.write("\n".join([", ".join(r) for r in rows]))
