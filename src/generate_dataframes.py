import numpy as np
import mysql.connector
import pandas as pd
import json
import os
from src import column_functions
from src.helpers.constants import (
    DEFAULT_SENSORS,
    UNITS,
    FILTER_SETTINGS,
    REPLACEMENT_DICT,
    ALL_GASES,
    ALL_SENSORS,
)
from .helpers.utils import replace_from_dict

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_OUT_DIR = f"{PROJECT_DIR}/data/csv-out"
with open(f"{PROJECT_DIR}/config.json") as f:
    config = json.load(f)

# TODO: document "movingWindowSize" and "outputStepSize"
# (moving window step size = time distance between resulting measurements)


def apply_statistical_filters(df, gas, column):
    return column_functions.filter_DataStat(
        df,
        gas=gas,
        column=column,
        clu_int=np.round(config["filter"]["outputStepSizeMinutes"] / 60, 6),
        drop_clu_info=FILTER_SETTINGS["drop_clu_info"],
        clu_str=FILTER_SETTINGS["cluster_start"],
        clu_end=FILTER_SETTINGS["cluster_end"],
        clu_win=np.round(config["filter"]["movingWindowSizeMinutes"] / 60, 6),
        case=config["filter"]["cases"],
    )


def save_to_csv(dataframe, date_string, replacement_dict):
    with open(f"{PROJECT_DIR}/data/csv-header-template.csv", "r") as template_file:
        with open(f"{CSV_OUT_DIR}/{date_string}.csv", "w") as out_file:
            fillParameters = replace_from_dict(replacement_dict)
            out_file.writelines(
                list(map(fillParameters, template_file.readlines())))
            dataframe.to_csv(out_file)


def get_calibration_replacement_dict(df_calibration, date_string):
    CALIBRATION_REPLACEMENT_DICT = {}

    df_calibration["ID"] = df_calibration["ID_SpectrometerCalibration"].map(
        lambda s: s[9:]
    )
    df_cali = df_calibration.replace(
        [np.inf, np.nan], 21000101).replace(["me17"], "me")
    df_cali["StartDate"] = df_cali["StartDate"].astype(int)
    df_cali["EndDate"] = df_cali["EndDate"].astype(int)
    df_cali = df_cali[df_cali["StartDate"].astype(str) <= date_string]
    df_cali = df_cali[df_cali["EndDate"].astype(str) >= date_string]
    df_cali = df_cali.sort_values(by="StartDate")

    def get_cal(s): return df_cali[df_cali["ID"].astype(str) == s].iloc[-1]

    for gas in ALL_GASES:
        for sensor in ALL_SENSORS:
            try:
                cal = get_cal(sensor)[f"{gas}_calibrationFactor"]
            except:
                cal = "NaN"
            CALIBRATION_REPLACEMENT_DICT.update(
                {f"CALIBRATION_{sensor}_{gas}": cal})

    return CALIBRATION_REPLACEMENT_DICT


def read_from_database(date_string, remove_calibration_data=True):
    db_connection = mysql.connector.connect(
        **config["authentication"]["mysql"])

    def read(sql_string): return pd.read_sql(sql_string, con=db_connection)

    date_query = f"(Date = {date_string})"
    location_tuple = ", ".join(
        map(lambda s: '"' + s + '"', config["input"]["locations"])
    )
    location_query = f"(ID_Location in ({location_tuple}))"

    if remove_calibration_data:
        setup_query = " OR ".join(
            [
                f'((ID_Location = "{l}") AND (ID_Spectrometer = "{DEFAULT_SENSORS[l]}"))'
                for l in DEFAULT_SENSORS.keys()
            ]
        )
        location_query += f" AND ({setup_query})"

    df_all = read(
        f"""
        SELECT *
        FROM measuredValues
        WHERE {date_query} AND {location_query}
        ORDER BY Hour
        """
    )
    # df_all.loc[df_all.Date <= 20170410, "xco_ppb"] = 0
    df_calibration = read("SELECT * FROM spectrometerCalibrationFactor")
    df_location = read("SELECT * FROM location")
    df_spectrometer = read("SELECT * FROM spectrometer")

    db_connection.close()

    return df_all, df_calibration, df_location, df_spectrometer


def filter_dataframes(df_calibrated):
    output_dataframes = {
        "raw": {gas: None for gas in ALL_GASES},
        "filtered": {gas: None for gas in ALL_GASES},
    }

    for case in ["raw", "filtered"]:

        # Physical Filter ----------------------
        if case == "filtered":
            df_filtered = (
                df_calibrated.groupby(["Date", "ID_Spectrometer"])
                .apply(
                    lambda x: column_functions.filterData(
                        x,
                        FILTER_SETTINGS["fvsi_threshold"],
                        FILTER_SETTINGS["sia_threshold"],
                        FILTER_SETTINGS["sza_threshold"],
                        FILTER_SETTINGS["step_size"],
                        FILTER_SETTINGS["o2_error"],
                        FILTER_SETTINGS["flag"],
                    )
                    if x.empty == False
                    else x
                )
                .drop(["Date", "ID_Spectrometer"], axis=1)
                .droplevel(level=2)
            )
        else:
            df_filtered = df_calibrated.set_index(["Date", "ID_Spectrometer"])

        for gas in ALL_GASES:
            COLUMN = f"x{gas}_{UNITS[gas]}"
            df_filtered_dropped = df_filtered.drop(
                columns=[f"x{g}_{UNITS[g]}" for g in ALL_GASES if g != gas]
            )
            if gas == "co":
                df_tmp = df_filtered.dropna(subset=[COLUMN])
                df_filtered = df_tmp.loc[df_tmp[COLUMN] < 200].copy()
            if gas == "ch4":
                # parameter needed for air mass correction
                df_filtered_dropped["elevation_angle"] = (
                    90 - df_filtered_dropped["asza_deg"]
                )

                # The sub operation below required the index to be unique
                # This line fixed the issue I experienced. Error message from before:
                # "cannot handle a non-unique multi-index!"
                df_filtered_dropped = df_filtered_dropped.reset_index().set_index(
                    ["Date", "ID_Spectrometer", "Hour"]
                )
                df_filtered_dropped[f"{COLUMN}_sub_mean"] = df_filtered_dropped.sub(
                    df_filtered_dropped[[COLUMN]].groupby(level=[0, 1]).mean()
                )[COLUMN]

            # Filter based on data statistics ----------------
            if (case == "filtered") and (not df_filtered_dropped.empty):
                df_filtered_statistical = apply_statistical_filters(
                    df_filtered_dropped, f"x{gas}", COLUMN
                )
            else:
                df_filtered_statistical = df_filtered_dropped.drop(
                    columns=["ID_Location"]
                )

            # Add Column ID_Location
            df_complete = df_filtered_statistical.join(
                (
                    df_filtered[["ID_Location"]]
                    .reset_index()
                    .drop_duplicates(ignore_index=True)
                    .set_index(["Date", "ID_Spectrometer"])
                )
            )

            # airmass correction for ch4
            if gas == "ch4":
                df_complete = column_functions.airmass_corr(
                    df_complete, clc=True, big_dataSet=False
                ).drop(
                    [
                        f"{COLUMN}_sub_mean",
                        "elevation_angle",
                    ],
                    axis=1,
                )

            output_dataframes[case][gas] = df_complete

    for case in ["raw", "filtered"]:
        for gas in ALL_GASES:
            assert output_dataframes[case][gas] is not None

    return output_dataframes


def run(date_string):
    # Each of the values of "withCal..."/"withoutCal..." looks like this:
    # {
    #    "raw": {"xco2": None, "xch4": None, "xco": None},
    #    "filtered": {"xco2": None, "xch4": None, "xco": None},
    #     "meta": {
    #         "dfLocation": ...,
    #         "replacementDict": ...,
    #     }
    # }
    dataframes = {
        "withCalibrationDays": None,
        "withoutCalibrationDays": None,
    }

    for calibrationCase in dataframes.keys():
        df_all, df_calibration, df_location, _ = read_from_database(
            date_string,
            remove_calibration_data=(
                calibrationCase == "withoutCalibrationDays"),
        )

        if not df_all.empty:
            df_calibrated, _ = column_functions.hp.calibration(
                df_all, df_calibration)

            dataframes[calibrationCase] = {
                **filter_dataframes(df_calibrated),
                "meta": {
                    "dfLocation": df_location,
                    "replacementDict": {
                        **REPLACEMENT_DICT,
                        **get_calibration_replacement_dict(df_calibration, date_string),
                    },
                },
            }

    return dataframes
