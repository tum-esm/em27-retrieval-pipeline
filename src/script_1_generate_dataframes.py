import sys
import numpy as np
import mysql.connector
import pandas as pd
import json
import os
from src import dataframe_processing
from src.utils.constants import (
    DEFAULT_SPECTROMETERS,
    UNITS,
    FILTER_SETTINGS,
    REPLACEMENT_DICT,
    ALL_GASES,
    ALL_SENSORS,
)
from rich.console import Console

console = Console()

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_OUT_DIR = f"{PROJECT_DIR}/data/csv-out"
with open(f"{PROJECT_DIR}/config.json") as f:
    config = json.load(f)


def _apply_statistical_filters(df, gas):
    return dataframe_processing.apply_statistical_filter(
        df,
        gas,
        cluster_output_step_size=np.round(
            config["filter"]["outputStepSizeMinutes"] / 60, 6
        ),
        drop_clusterpoints_info=FILTER_SETTINGS["drop_clusterpoints_info"],
        cluster_window_size=np.round(
            config["filter"]["movingWindowSizeMinutes"] / 60, 6
        ),
        filter_cases=config["filter"]["cases"],
    )


def _get_calibration_replacement_dict(df_calibration: pd.DataFrame, date_string: str):
    CALIBRATION_REPLACEMENT_DICT = {}

    df_calibration["ID"] = df_calibration["ID_SpectrometerCalibration"].map(
        lambda s: s[9:]
    )
    df_cali = df_calibration.replace([np.inf, np.nan], 21000101).replace(["me17"], "me")
    df_cali["StartDate"] = df_cali["StartDate"].astype(int)
    df_cali["EndDate"] = df_cali["EndDate"].astype(int)
    df_cali = df_cali[df_cali["StartDate"].astype(str) <= date_string]
    df_cali = df_cali[df_cali["EndDate"].astype(str) >= date_string]
    df_cali = df_cali.sort_values(by="StartDate")

    for gas in ALL_GASES:
        for sensor in ALL_SENSORS:
            try:
                cal = (df_cali[df_cali["ID"].astype(str) == sensor].iloc[-1])[
                    f"{gas}_calibrationFactor"
                ]
            except:
                cal = "NaN"
            CALIBRATION_REPLACEMENT_DICT.update({f"CALIBRATION_{sensor}_{gas}": cal})

    return CALIBRATION_REPLACEMENT_DICT


def _read_from_database(date_string, remove_calibration_data=True):
    db_connection = mysql.connector.connect(
        **config["authentication"]["mysql"], auth_plugin="mysql_native_password"
    )

    def read(sql_string):
        return pd.read_sql(sql_string, con=db_connection)

    date_query = f"(Date = {date_string})"
    location_tuple = ", ".join([f'"{l}"' for l in config["input"]["locations"]])
    location_query = f"(ID_Location in ({location_tuple}))"

    if remove_calibration_data:
        setup_query = " OR ".join(
            [
                f'((ID_Location = "{l}") AND (ID_Spectrometer = "{DEFAULT_SPECTROMETERS[l]}"))'
                for l in DEFAULT_SPECTROMETERS.keys()
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


def _filter_dataframes(df_calibrated):
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
                    lambda x: dataframe_processing.apply_physical_filter(
                        x,
                        fvsi_threshold=FILTER_SETTINGS["fvsi_threshold"],
                        sia_threshold=FILTER_SETTINGS["sia_threshold"],
                        sza_threshold=FILTER_SETTINGS["sza_threshold"],
                        step_size=FILTER_SETTINGS["step_size"],
                        o2_error=FILTER_SETTINGS["o2_error"],
                        flag=FILTER_SETTINGS["flag"],
                    )
                )
                .drop(["Date", "ID_Spectrometer"], axis=1)
                .droplevel(level=2)
            )
        else:
            df_filtered = df_calibrated.set_index(["Date", "ID_Spectrometer"])

        for gas in ALL_GASES:
            COLUMN = f"x{gas}_{UNITS[gas]}"
            df_filtered_dropped: pd.DataFrame = df_filtered.drop(
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
                df_filtered_statistical = _apply_statistical_filters(
                    df_filtered_dropped, f"x{gas}"
                )
                if len(list(df_filtered_statistical.columns)) == 0:
                    df_filtered_statistical = (
                        pd.DataFrame(
                            columns=[
                                c
                                for c in df_filtered_dropped.columns
                                if c != "ID_Location"
                            ]
                        )
                        .reset_index()
                        .set_index(["Date", "ID_Spectrometer", "Hour"])
                    )
            else:
                df_filtered_statistical: pd.DataFrame = df_filtered_dropped.drop(
                    columns=["ID_Location"]
                )

            try:
                # Add Column ID_Location
                df_complete = df_filtered_statistical.join(
                    (
                        df_filtered[["ID_Location"]]
                        .reset_index()
                        .drop_duplicates(ignore_index=True)
                        .set_index(["Date", "ID_Spectrometer"])
                    )
                )
            except Exception:
                console.print_exception(show_locals=True)
                sys.exit()

            # airmass correction for ch4
            if gas == "ch4":
                df_complete = dataframe_processing.apply_airmass_correction(
                    df_complete
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
        df_all, df_calibration, df_location, _ = _read_from_database(
            date_string,
            remove_calibration_data=(calibrationCase == "withoutCalibrationDays"),
        )

        if not df_all.empty:
            df_calibrated, _ = dataframe_processing.apply_calibration(
                df_all, df_calibration
            )

            dataframes[calibrationCase] = {
                **_filter_dataframes(df_calibrated),
                "meta": {
                    "dfLocation": df_location,
                    "replacementDict": {
                        **REPLACEMENT_DICT,
                        **_get_calibration_replacement_dict(
                            df_calibration, date_string
                        ),
                    },
                },
            }

    return dataframes
