import os
import pandas as pd
from .helpers.utils import ls_ext, str_to_ts, hour_to_ts, concat, unique
from rich.progress import track


PLOT_LOCATIONS = ["TUM_I", "TAU", "GR\u00c4", "OBE", "FEL"]
GASES = ["co2", "ch4"]
UNITS = ["ppm", "ppm"]

data_dir = os.path.join(os.path.dirname(__file__), "../data")


def run():
    """
    Convert data in `data/csv-in` to `data/csv-out`.

    Examples in the README.md.
    """

    gas_days = [
        list(map(lambda s: s[:8], ls_ext(f"{data_dir}/csv-in", f"{gas}.csv")))
        for gas in GASES
    ]
    total_days = unique(concat(gas_days))
    # Now: gas_days = [['20201214', ...], ['20201214', ...]]
    # Now: total_days = ['20201214', ...]

    for day in track(total_days, description="Transform csv"):

        day_timestamp = str_to_ts(day)

        # Which gases (with corresponding units) are available for this day
        day_gases = []
        day_units = []
        for i in range(len(GASES)):
            if day in gas_days[i]:
                day_gases.append(GASES[i])
                day_units.append(UNITS[i])
        if len(day_gases) != len(GASES):
            print(
                f"WARNING: On day {day}, only the following "
                + f"gas-csv's have been found: {day_gases}"
            )

        # Load dataframe from csv and get rid of unused columns
        gas_dfs = list(
            map(
                lambda df: df.loc[:, ~df.columns.str.contains("^Unnamed")].drop(
                    columns=["Date", "xh2o_ppm", "Direction", "TimeStamp"]
                ),
                [
                    pd.read_csv(f"{data_dir}/csv-in/{day}_x{gas}.csv")
                    for gas in day_gases
                ],
            )
        )

        # Refactor hour column
        new_gas_dfs = []
        for df in gas_dfs:
            df["Hour"] = df["Hour"].apply(lambda hour: hour_to_ts(day_timestamp, hour))
            new_gas_dfs.append(df.rename(columns={"Hour": "timestamp"}))

        gas_dfs = new_gas_dfs

        # One row for every timestamp where any measurement has been logged
        merged_df = pd.DataFrame(
            data={
                "timestamp": unique(concat([list(df["timestamp"]) for df in gas_dfs]))
            }
        ).sort_values(by=["timestamp"])

        for i in range(len(day_gases)):
            df = gas_dfs[i]

            # If there is more than one spectrometer located at TUM_I
            # -> Assert that 'ma61' is one of them and get rid of the others
            tum_spectrometers = list(
                filter(
                    lambda s: isinstance(s, str),
                    pd.unique(
                        df.where(df["ID_Location"] == "TUM_I")["ID_Spectrometer"]
                    ),
                )
            )
            if len(tum_spectrometers) > 1:
                assert (
                    "ma61" in tum_spectrometers
                ), f"More than one sensor at TUM_I but 'ma61' not found: {tum_spectrometers}"
                df2 = df.where(df["ID_Location"] == "TUM_I").dropna()
                df3 = df2.where(df2["ID_Spectrometer"] != "ma61").dropna()
                df = df.drop(df3.index)
                del df2, df3

            # The spectrometer is now irrelevant
            df = df.drop(columns=["ID_Spectrometer"])

            for location in PLOT_LOCATIONS:

                # Get all not NaN rows at this location
                location_df = (
                    df.where(df["ID_Location"] == location)
                    .dropna()
                    .drop(columns=["ID_Location"])
                )

                # Merge this location timeseries into the merged dataframe
                location = location.replace("\u00c4", "A")
                location_df = location_df.rename(
                    columns={
                        f"x{day_gases[i]}_{day_units[i]}": f"{location}_x{day_gases[i]}"
                    }
                )
                merged_df = merged_df.merge(
                    location_df, left_on="timestamp", right_on="timestamp", how="left"
                ).fillna(value=0)

        # Save merged dataframe in csv file
        merged_df = merged_df.round(5).sort_values(by=["timestamp"])
        merged_df.to_csv(
            f"{data_dir}/csv-out/{day}_xco2_xch4.csv", index=False, header=True
        )
