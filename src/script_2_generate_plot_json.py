import os
import pandas as pd
from .helpers.utils import ls_ext, str_to_ts, hour_to_ts, concat, unique
from rich.progress import track
import sys
import json

# same level as pyproject.toml
project_dir = "/".join(__file__.split("/")[:-2])
data_dir = f"{project_dir}/data"

with open(f"{project_dir}/config.json") as f:
    config = json.load(f)
    assert type(config["stations"]) == list
    assert all(type(g) == dict for g in config["stations"])
    assert all(type(g["location"]) == str and type(g["sensor"]) == str for g in config["stations"])
    assert type(config["gases"]) == list
    assert all(type(g) == dict for g in config["gases"])
    assert all(type(g["name"]) == str and type(g["unit"]) == str for g in config["gases"])
    LOCATIONS = [s["location"] for s in config["stations"]]
    GASES = [g["name"] for g in config["gases"]]


def run():
    """
    Convert data in `data/csv-in` to `data/csv-out`.

    Examples in the README.md.
    """

    all_day_strings = unique(
        [s[:8] for s in ls_ext(f"{data_dir}/csv-in", ".csv") if s[:8].isnumeric()]
    )
    # all_day_strings = ['20201214', ...]
    print(all_day_strings)

    for day_string in track(all_day_strings, description="Transform csv"):

        day_plot_data = {}
        filtered_dfs, raw_dfs = {}, {}

        for gas in GASES:
            for raw in [True, False]:
                csv_file = (
                    f"{data_dir}/csv-in/{day_string}_{gas}{'_raw' if raw else ''}.csv"
                )
                if os.path.isfile(csv_file):
                    (raw_dfs if raw else filtered_dfs).update(
                        {gas: pd.read_csv(csv_file)}
                    )

        filtered_hours = unique(
            concat([list(filtered_dfs[gas]["hour"]) for gas in filtered_dfs])
        )
        raw_hours = unique(concat([list(raw_dfs[gas]["hour"]) for gas in raw_dfs]))

        filtered_hours.sort()
        raw_hours.sort()

        filtered_hour_df = pd.DataFrame(filtered_hours, columns=["hour"])
        raw_hour_df = pd.DataFrame(raw_hours, columns=["hour"])

        if len(filtered_dfs) > 0:
            day_plot_data.update(
                {
                    "hours": list(filtered_hour_df["hour"]),
                    "timeseries": [],
                }
            )
        if len(raw_dfs) > 0:
            day_plot_data.update(
                {
                    "rawHours": list(raw_hour_df["hour"]),
                    "rawTimeseries": [],
                    "flagTimeseries": [],
                }
            )

        for location in LOCATIONS:
            for gas in filtered_dfs:
                timeseries_df = filtered_dfs[gas].loc[
                    (filtered_dfs[gas]["location"] == location)
                ]
                if not timeseries_df.empty:
                    day_plot_data["timeseries"].append(
                        {
                            "gas": gas,
                            "location": location,
                            "data": list(
                                filtered_hour_df.set_index("hour")
                                .join(timeseries_df.set_index("hour"))
                                .fillna(0)["x"]
                            ),
                        }
                    )
            # only one flag timeseries per day (flags are the same for every gas)
            flags_added = False

            for gas in raw_dfs:
                timeseries_df = raw_dfs[gas].loc[(raw_dfs[gas]["location"] == location)]
                if not timeseries_df.empty:
                    day_plot_data["rawTimeseries"].append(
                        {
                            "gas": gas,
                            "location": location,
                            "data": list(
                                raw_hour_df.set_index("hour")
                                .join(timeseries_df.set_index("hour"))
                                .fillna(0)["x"]
                            ),
                        }
                    )
                    if not flags_added:
                        day_plot_data["flagTimeseries"].append(
                            {
                                "location": location,
                                "data": list(
                                    raw_hour_df.set_index("hour")
                                    .join(timeseries_df.set_index("hour"))
                                    .fillna(0)["flag"]
                                ),
                            }
                        )
                        flags_added = True

        with open(f"{data_dir}/json-out/{day_string}.json", "w") as f:
            json.dump({
                "date": day_string,
                "data": day_plot_data
            }, f, indent=2)
