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
    assert all(
        type(g["location"]) == str and type(g["sensor"]) == str
        for g in config["stations"]
    )
    assert type(config["gases"]) == list
    assert all(type(g) == dict for g in config["gases"])
    assert all(
        type(g["name"]) == str and type(g["unit"]) == str for g in config["gases"]
    )
    LOCATIONS = [s["location"] for s in config["stations"]]
    GASES = [g["name"] for g in config["gases"]]


def run(minify=True):
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

        if len(filtered_dfs) > 0:
            day_plot_data.update(
                {
                    "timeseries": [],
                }
            )
        if len(raw_dfs) > 0:
            day_plot_data.update(
                {
                    "rawTimeseries": [],
                    "flagTimeseries": [],
                }
            )

        for location in LOCATIONS:
            for gas in filtered_dfs:
                timeseries_df = (
                    filtered_dfs[gas]
                    .loc[(filtered_dfs[gas]["location"] == location)]
                    .set_index("hour")
                    .sort_index()
                    .reset_index()
                )
                if not timeseries_df.empty:
                    day_plot_data["timeseries"].append(
                        {
                            "gas": gas,
                            "location": location,
                            "count": timeseries_df.shape[0],
                            "data": {
                                "xs": list(timeseries_df["hour"]),
                                "ys": list(timeseries_df["x"]),
                            },
                        }
                    )
            # only one flag timeseries per day (flags are the same for every gas)
            flags_added = False

            for gas in raw_dfs:
                timeseries_df = (
                    raw_dfs[gas]
                    .loc[(raw_dfs[gas]["location"] == location)]
                    .set_index("hour")
                    .sort_index()
                    .reset_index()
                )
                if not timeseries_df.empty:
                    day_plot_data["rawTimeseries"].append(
                        {
                            "gas": gas,
                            "location": location,
                            "count": timeseries_df.shape[0],
                            "data": {
                                "xs": list(timeseries_df["hour"]),
                                "ys": list(timeseries_df["x"]),
                            },
                        }
                    )
                    if not flags_added:
                        day_plot_data["flagTimeseries"].append(
                            {
                                "location": location,
                                "count": timeseries_df.shape[0],
                                "data": {
                                    "xs": list(timeseries_df["hour"]),
                                    "ys": list(timeseries_df["flag"]),
                                },
                            }
                        )
                        flags_added = True

        with open(f"{data_dir}/json-out/{day_string}.json", "w") as f:
            json_string = json.dumps(
                {"date": day_string, "data": day_plot_data}, indent=2
            )
            if minify:
                json_string = json_string.replace(" ", "").replace("\n", "")
                print(len(json_string))
            f.write(json_string)
