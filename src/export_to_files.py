import json
import pandas as pd
import os
import sys

from src.helpers.constants import DEFAULT_SENSORS
from .helpers.utils import concat, unique, hour_to_timestring, replace_from_dict


PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(f"{PROJECT_DIR}/config.json") as f:
    config = json.load(f)


def as_csv(day_string, dataframes):
    # dataframes looks like this:
    # {
    #    "raw": {"co2": None, "ch4": None, "co": None},
    #    "filtered": {"co2": None, "ch4": None, "co": None},
    #     "meta": {
    #         "dfLocation": ...,
    #         "replacementDict": ...,
    #     }
    # }
    output_dfs = {}

    for gas in config["input"]["gases"]:
        df_corrected_inversion = (
            dataframes["filtered"][gas]
            .reset_index()
            .set_index(["ID_Location"])
            .join(
                dataframes["meta"]["dfLocation"].set_index(["ID_Location"])[
                    ["Direction"]
                ]
            )
            .reset_index()
        )

        # drop unused columns
        output_dfs[gas] = df_corrected_inversion.drop(
            columns=list(
                filter(
                    lambda c: c in df_corrected_inversion.columns,
                    [
                        "ID_Location",
                        "Direction",
                        "xh2o_ppm",
                        "fvsi",
                        "sia_AU",
                        "asza_deg",
                        "flag",
                        "pout_hPa",
                        "pins_mbar",
                        "xo2_error",
                        "column_o2",
                        "column_h2o",
                        "column_air",
                        "xair",
                        "month",
                        "year",
                        "Date",
                    ],
                )
            )
        )

    # use "Hour" column (timestamp) as index to merge data on
    merged_df = (
        pd.DataFrame(
            sorted(
                unique(
                    concat(
                        [
                            list(output_dfs[gas]["Hour"])
                            for gas in config["input"]["gases"]
                        ]
                    )
                )
            ),
            columns=["Hour"],
        )
        .applymap(lambda x: hour_to_timestring(day_string, x))
        .set_index(["Hour"])
    )

    for gas in config["input"]["gases"]:
        output_dfs[gas]["Hour"] = output_dfs[gas]["Hour"].map(
            lambda x: hour_to_timestring(day_string, x)
        )

        for spectrometer in [DEFAULT_SENSORS[l] for l in config["input"]["locations"]]:
            df = (
                (
                    output_dfs[gas]
                    .loc[(output_dfs[gas]["ID_Spectrometer"] == spectrometer)]
                    .rename(
                        columns={
                            f"x{gas}_ppm": f"{spectrometer}_x{gas}_sc",
                        }
                    )
                )
                .set_index("Hour")
                .drop(columns=["ID_Spectrometer"])
            )
            merged_df = merged_df.merge(
                df,
                how="left",
                left_on="Hour",
                right_on="Hour",
            )

    ACTUAL_LOCATIONS = {}
    for [location, sensor] in list(
        (df_corrected_inversion[["ID_Location", "ID_Spectrometer"]])
        .drop_duplicates()
        .values.tolist()
    ):
        ACTUAL_LOCATIONS.update({sensor: location})

    LOCATION_HEADER_ROWS = []
    for sensor in [DEFAULT_SENSORS[l] for l in config["input"]["locations"]]:
        if sensor in ACTUAL_LOCATIONS:
            LOCATION_HEADER_ROWS.append(f"##    {sensor}: {ACTUAL_LOCATIONS[sensor]}")
        else:
            LOCATION_HEADER_ROWS.append(f"##    {sensor}: unknown (no data)")

    with open(f"{PROJECT_DIR}/data/csv-header-template.csv", "r") as template_file:
        with open(f"{PROJECT_DIR}/data/csv-out/{day_string}.csv", "w") as out_file:
            fillParameters = replace_from_dict(
                {
                    **dataframes["meta"]["replacementDict"],
                    "SENSOR_LOCATIONS": "\n".join(LOCATION_HEADER_ROWS),
                }
            )
            out_file.writelines(list(map(fillParameters, template_file.readlines())))
            merged_df.fillna("NaN").reset_index().rename(
                columns={"Hour": "year_day_hour"}
            ).set_index(["year_day_hour"]).to_csv(out_file)


def as_json():
    # TODO: Create tmp directory
    # TODO: Save raw and filtered CSVs
    # TODO: Convert CSVs to JSON
    # TODO: Remove tmp directory
    pass
