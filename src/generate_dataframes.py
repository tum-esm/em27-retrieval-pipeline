import numpy as np
import mysql.connector
import pandas as pd
import json
import datetime
import sys
import os
from src import column_functions
from .helpers.utils import unique, hour_to_timestring, get_commit_sha, replace_from_dict


# load config
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_OUT_DIR = f"{PROJECT_DIR}/data/csv-out"
with open(f"{PROJECT_DIR}/config.json") as f:
    config = json.load(f)

UNITS = {
    "co2": "ppm",
    "ch4": "ppm",
    "co": "ppb",
}

# set parameters
# 1. basic filter settings
fvsi_thold = 5  # fractional variation in solar intensity < the value - before: 4
sia_thold = 0.4  # solar intensity average > value
sza_thold = 75  # solar zenith angle < value
o2_error = 0.0005
step_size = 0.1
flag = 1

# 2. advanced filter settings
cluster_interval = np.round(
    1 / 30, 6
)  # [h], moving window step size -> time distance between resulting measurements
cluster_window = np.round(1 / 6, 6)  # [h], moving window size
cluster_start = 4  # Time in UTC, start time for the use of measurements
cluster_end = 18  # Time in UTC, end time for the use of measurements


# DROP_CLU_INFO -> version of dropping the averaged points with low information contend
# drop_clu_info["version"] = 104  # 'calculation' or Number of maximal measurement points per averaged point (10min interval=104)
# drop_clu_info["percent"] = 0.2  # [0,1] only needed when 'version' is equal to 'percent'


def apply_statistical_filters(df, gas, column):
    return column_functions.filter_DataStat(
        df,
        gas=gas,
        column=column,
        clu_int=cluster_interval,
        drop_clu_info={"drop": True, "version": 104, "percent": 0.2},
        clu_str=cluster_start,
        clu_end=cluster_end,
        clu_win=cluster_window,
        case=["outlier", "rollingMean"],  # , "continuous", "interval"],
    )


def save_to_csv(dataframe, date_string, replacement_dict):
    with open(f"{PROJECT_DIR}/data/csv-header-template.csv", "r") as template_file:
        with open(f"{CSV_OUT_DIR}/{date_string}.csv", "w") as out_file:
            fillParameters = replace_from_dict(replacement_dict)
            out_file.writelines(list(map(fillParameters, template_file.readlines())))
            dataframe.to_csv(out_file)


REPLACEMENT_DICT = {
    "AUTHOR_NAMES": ", ".join(
        list(map(lambda a: a["name"], config["meta"]["authors"]))
    ),
    "CONTACT_EMAILS": ", ".join(
        list(map(lambda a: a["email"], config["meta"]["authors"]))
    ),
    "GENERATION_DATE": str(datetime.datetime.now()) + " UTC",
    "CODE_REPOSITORY": config["meta"]["codeRepository"],
    "COMMIT_SHA": get_commit_sha(),
    "SETTING_fvsi_thold": fvsi_thold,
    "SETTING_sia_thold": sia_thold,
    "SETTING_sza_thold": sza_thold,
    "SETTING_o2_error": o2_error,
    "SETTING_step_size": step_size,
    "SETTING_flag": flag,
}


def get_calibration_replacement_dict(df_calibration, date_string):
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

    get_cal = lambda s: df_cali[df_cali["ID"].astype(str) == s].iloc[-1]

    for gas in ["co2", "ch4", "co"]:
        for station in ["ma", "mb", "mc", "md", "me"]:
            try:
                cal = get_cal(station)[f"{gas}_calibrationFactor"]
            except:
                cal = "NaN"
            CALIBRATION_REPLACEMENT_DICT.update({f"CALIBRATION_{station}_{gas}": cal})

    return CALIBRATION_REPLACEMENT_DICT


def read_from_database(date_string, remove_calibration_data=True):
    db_connection = mysql.connector.connect(**config["authentication"]["mysql"])
    read = lambda sql_string: pd.read_sql(sql_string, con=db_connection)

    # TODO: Hardcode calibration station/location combinations
    # TODO: Use locations from config.json

    if remove_calibration_data:
        df_all = read(
            f"""
            SELECT *
            FROM measuredValues
            WHERE (Date = {date_string}) AND
            (ID_Location in ('GEO', 'ROS', 'JOR', 'HAW')) AND
            ((ID_Location != 'GEO') OR (ID_Spectrometer = 'me17'))
            ORDER BY Hour
            """
        )
    else:
        df_all = read(
            f"""
            SELECT *
            FROM measuredValues
            WHERE (Date = {date_string}) AND
            (ID_Location in ('GEO', 'ROS', 'JOR', 'HAW'))
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
        "raw": {"co2": None, "ch4": None, "co": None},
        "filtered": {"co2": None, "ch4": None, "co": None},
    }

    for case in ["raw", "filtered"]:

        ## Physical Filter ----------------------
        if case == "filtered":
            df_filtered = (
                df_calibrated.groupby(["Date", "ID_Spectrometer"])
                .apply(
                    lambda x: column_functions.filterData(
                        x, fvsi_thold, sia_thold, sza_thold, step_size, o2_error, flag
                    )
                    if x.empty == False
                    else x
                )
                .drop(["Date", "ID_Spectrometer"], axis=1)
                .droplevel(level=2)
            )
        else:
            df_filtered = df_calibrated.set_index(["Date", "ID_Spectrometer"])

        for gas in ["co2", "ch4", "co"]:
            COLUMN = f"x{gas}_{UNITS[gas]}"
            df_filtered_dropped = df_filtered.drop(
                columns=[f"x{g}_{UNITS[g]}" for g in ["co2", "ch4", "co"] if g != gas]
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

            ## Filter based on data statistics ----------------
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

            ## airmass correction for ch4
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
        for gas in ["co2", "ch4", "co"]:
            assert output_dataframes[case][gas] is not None

    return output_dataframes


"""
def filter_and_return(date_string, df_calibrated, df_location, case):

    # TODO: split function!
    assert case in ["website-raw", "website-filtered", "inversion-filtered"]

    ## Physical Filter ----------------------
    if case in ["website-filtered", "inversion-filtered"]:
        df_filtered = (
            df_calibrated.groupby(["Date", "ID_Spectrometer"])
            .apply(
                lambda x: column_functions.filterData(
                    x, fvsi_thold, sia_thold, sza_thold, step_size, o2_error, flag
                )
                if x.empty == False
                else x
            )
            .drop(["Date", "ID_Spectrometer"], axis=1)
            .droplevel(level=2)
        )
    else:
        df_filtered = df_calibrated.set_index(["Date", "ID_Spectrometer"])

    # TODO: break into smaller loops
    # TODO: use dict as datastructure
    ## Gas seperated code ---------
    for gas in ["xco2", "xch4", "xco"]:
        COLUMN = f"{gas}_{UNITS[gas]}"
        if gas == "xco":
            df_tmp = df_filtered.dropna(subset=["xco_ppb"])
            df_filtered = df_tmp.loc[df_tmp["xco_ppb"] < 200].copy()

        df_filtered_dropped = df_filtered.drop(
            columns=[f"{g}_{UNITS[g]}" for g in ["xco2", "xch4", "xco"] if g != gas]
        )

        if gas == "xch4":
            # parameter needed for air mass correction
            df_filtered_dropped["elevation_angle"] = (
                90 - df_filtered_dropped["asza_deg"]
            )

            # The sub operation below required the index to be unique
            # This line fixed the issue I experienced. Error message from before:
            # "cannot handle a non-unique multi-index!"
            df_filtered = df_filtered_dropped.reset_index().set_index(
                ["Date", "ID_Spectrometer", "Hour"]
            )
            df_filtered_dropped["xch4_ppm_sub_mean"] = df_filtered_dropped.sub(
                df_filtered_dropped[[COLUMN]].groupby(level=[0, 1]).mean()
            )[COLUMN]

        ## Filter based on data statistics ----------------
        if (case in ["website-filtered", "inversion-filtered"]) and (
            not df_filtered_dropped.empty
        ):
            df_filtered_statistical = apply_statistical_filters(
                df_filtered_dropped, gas, COLUMN
            )
        else:
            df_filtered_statistical = df_filtered_dropped.drop(columns=["ID_Location"])

        # Add Column ID_Location
        df_all_inf = df_filtered_statistical.join(
            (
                df_filtered[["ID_Location"]]
                .reset_index()
                .drop_duplicates(ignore_index=True)
                .set_index(["Date", "ID_Spectrometer"])
            )
        )
        ## airmass correction and removing useless columns -----------
        if gas == "xch4":
            df_corrected_inversion = column_functions.airmass_corr(
                df_all_inf, clc=True, big_dataSet=False
            ).drop(
                [
                    "xch4_ppm_sub_mean",
                    "elevation_angle",
                ],
                axis=1,
            )
        else:
            df_corrected_inversion = df_all_inf

        # TODO: cut here maybe?

        # Website (raw + filtered)
        if case in ["website-raw", "website-filtered"]:
            df_corrected_website = df_corrected_inversion.drop(
                [
                    "fvsi",
                    "sia_AU",
                    "asza_deg",
                    "xo2_error",
                    "pout_hPa",
                    "pins_mbar",
                    "column_o2",
                    "column_h2o",
                    "column_air",
                    "xair",
                    "xh2o_ppm",
                ],
                axis=1,
            )

            df_corrected_website = (
                df_corrected_website.reset_index()
                .set_index(["ID_Location"])
                .join(df_location.set_index(["ID_Location"])[["Direction"]])
                .reset_index()
            )
            columns_to_drop = ["Date", "ID_Location", "Direction"]
            if (case == "website-filtered") and (not df_corrected_website.empty):
                columns_to_drop += ["year", "month", "flag"]
                df_corrected_website.reset_index()
                df_corrected_website["Hour"] = df_corrected_website["Hour"].round(3)
            df_corrected_website.rename(
                columns={
                    "Hour": "hour",
                    "ID_Spectrometer": "sensor",
                    "xco2_ppm": "x",
                    "xch4_ppm": "x",
                },
                inplace=True,
            )
            df_corrected_website = (
                df_corrected_website.drop(columns=columns_to_drop)
                .set_index(["hour"])
                .sort_index()
            )

            if gas == "xco2":
                xco2 = df_corrected_website
            elif gas == "xch4":
                xch4 = df_corrected_website
            elif gas == "xco":
                xco = df_corrected_website

        # Inversion (only filtered)

        if case == "inversion-filtered":
            df_corrected_inversion = (
                df_corrected_inversion.reset_index()
                .set_index(["ID_Location"])
                .join(df_location.set_index(["ID_Location"])[["Direction"]])
                .reset_index()
            )

            columns_to_drop = [
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
            ]

            df_corrected_inversion = df_corrected_inversion.drop(
                columns=[
                    c for c in columns_to_drop if c in df_corrected_inversion.columns
                ]
            )

            # TODO: Use dict datastructure for different gas-dfs
            if gas == "xco2":
                inversion_xco2 = df_corrected_inversion
            elif gas == "xch4":
                inversion_xch4 = df_corrected_inversion

    if case == "inversion-filtered":

        inversion_hours = unique(
            list(inversion_xco2["Hour"]) + list(inversion_xch4["Hour"])
        )
        inversion_hour_df = (
            pd.DataFrame(sorted(inversion_hours), columns=["Hour"])
            .applymap(lambda x: hour_to_timestring(date_string, x))
            .set_index(["Hour"])
        )
        inversion_xch4["Hour"] = inversion_xch4["Hour"].map(
            lambda x: hour_to_timestring(date_string, x)
        )
        inversion_xco2["Hour"] = inversion_xco2["Hour"].map(
            lambda x: hour_to_timestring(date_string, x)
        )

        merged_df = inversion_hour_df

        # TODO: Use locations from config.json
        for spectrometer in ["mb86", "mc15", "md16", "me17"]:
            for df in [
                inversion_xch4.loc[(inversion_xch4["ID_Spectrometer"] == spectrometer)],
                inversion_xco2.loc[(inversion_xco2["ID_Spectrometer"] == spectrometer)],
            ]:
                df = df.rename(
                    columns={
                        "xch4_ppm": f"{spectrometer[:2]}_xch4_sc",
                        "xco2_ppm": f"{spectrometer[:2]}_xco2_sc",
                    }
                )
                merged_df = merged_df.merge(
                    df.set_index("Hour").drop(columns=["ID_Spectrometer"]),
                    how="left",
                    left_on="Hour",
                    right_on="Hour",
                )

        save_to_csv(
            merged_df.fillna("NaN")
            .reset_index()
            .rename(columns={"Hour": "year_day_hour"})
            .set_index(["year_day_hour"]),
            date_string,
            REPLACEMENT_DICT,
        )

    else:
        return xco, xco2, xch4
    # maybe edn function here and give 3 dataframes as output

    # new functions for saving or uploading into DB after transforming it to json
    # =============================================================================
    #   Add code to save &/or upload csvs to database here
    #   read in while csv maybe not to efficient
    #   Maybe later groupby date convert to json
    # =============================================================================
"""


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
            remove_calibration_data=(calibrationCase == "withoutCalibrationDays"),
        )

        if not df_all.empty:
            df_calibrated, _ = column_functions.hp.calibration(df_all, df_calibration)

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
