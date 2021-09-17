import numpy as np
import mysql.connector
import pandas as pd
import json
import datetime
import sys
import os
import subprocess
from src import column_functions
from .helpers.utils import unique, hour_to_timestring

## Set parameter ------------------------
# basic filter settings
fvsi_thold = 5  # fractional variation in solar intensity < the value - before: 4
sia_thold = 0.4  # solar intensity average > value
sza_thold = 75  # solar zenith angle < value
o2_error = 0.0005
step_size = 0.1
flag = 1

# advanced filter settings
cluster_interval = np.round(
    1 / 30, 6
)  # [h], moving window step size -> time distance between resulting measurements
cluster_window = np.round(1 / 6, 6)  # [h], moving window size
cluster_start = 4  # Time in UTC, start time for the use of measurements
cluster_end = 18  # Time in UTC, end time for the use of measurements

# version of dropping the averaged points with low information contend
version_ofDorp = {
    "drop": True,
    "version": 104,  # 'calculation' or Number of maximal measurement points per averaged point (10min interval=104)
    "percent": 0.2,  # [0,1] only needed when 'version' is equal to 'percent'
}

# same level as pyproject.toml
project_dir = "/".join(__file__.split("/")[:-2])
with open(f"{project_dir}/config.json") as f:
    config = json.load(f)
    assert type(config["mysql"]) == dict
    assert type(config["inversionCSV"]) == dict


commit_sha_process = subprocess.Popen(
    ["git", "rev-parse", "--verify", "HEAD"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
)
stdout, stderr = commit_sha_process.communicate()
COMMIT_SHA = stdout.decode().replace("\n", "").replace(" ", "")
assert len(COMMIT_SHA) > 0

replacement_dict = {
    "AUTHOR_NAMES": config["inversionCSV"]["authorNames"],
    "CONTACT_EMAILS": config["inversionCSV"]["contactEmails"],
    "GENERATION_DATE": str(datetime.datetime.now()) + " UTC",
    "CODE_REPOSITORY": config["inversionCSV"]["codeRepository"],
    "COMMIT_SHA": COMMIT_SHA,
    "SETTING_fvsi_thold": fvsi_thold,
    "SETTING_sia_thold": sia_thold,
    "SETTING_sza_thold": sza_thold,
    "SETTING_o2_error": o2_error,
    "SETTING_step_size": step_size,
    "SETTING_flag": flag,
}


def read_database(date_string, remove_calibration_data=True):
    db_connection = mysql.connector.connect(**config["mysql"])
    read = lambda sql_string: pd.read_sql(sql_string, con=db_connection)

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


# add timestamp
def Time_Stamp(df):
    df = df.drop(columns=["month", "year"])
    df = df.reset_index(drop=True)
    df["TimeStamp"] = [
        (
            datetime.datetime.strptime(str(df.Date[j]), "%Y%m%d")
            + datetime.timedelta(hours=df.Hour[j])
        )
        for j in range(len(df.Hour))
    ]
    return df.sort_values(by=["ID_Spectrometer", "TimeStamp"]).reset_index(drop=True)


def filter_and_return(date_string, df_calibrated, df_location, case):
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

    ## Gas seperated code ---------
    for gas in ["xco2", "xch4", "xco"]:
        if gas == "xco":
            column = "xco_ppb"
            # removing rows which do not contain any CO measurements
            df_temp = df_filtered.dropna(subset=["xco_ppb"])
            df_filtered = df_temp.loc[df_temp["xco_ppb"] < 200].copy()
            # drop columns of ch4 and co2
            df_filtered_droped = df_filtered.drop(columns=["xch4_ppm", "xco2_ppm"])
        elif gas == "xco2":
            column = "xco2_ppm"
            # drop columns of ch4 and co
            df_filtered_droped = df_filtered.drop(columns=["xch4_ppm", "xco_ppb"])
        elif gas == "xch4":
            column = "xch4_ppm"
            # drop columns of co and co2
            df_filtered_droped = df_filtered.drop(columns=["xco_ppb", "xco2_ppm"])
            # parameter needed for air mass correction
            df_filtered_droped["elevation_angle"] = 90 - df_filtered_droped["asza_deg"]

            # The sub operation below required the index to be unique
            # This line fixed the issue I experienced. Error message from before:
            # "cannot handle a non-unique multi-index!"
            df_filtered_droped = df_filtered_droped.reset_index().set_index(
                ["Date", "ID_Spectrometer", "Hour"]
            )
            df_filtered_droped["xch4_ppm_sub_mean"] = df_filtered_droped.sub(
                df_filtered_droped[["xch4_ppm"]].groupby(level=[0, 1]).mean()
            )["xch4_ppm"]
        else:
            raise Exception

        ## Filter based on data statistics ----------------
        if (case in ["website-filtered", "inversion-filtered"]) and (
            not df_filtered_droped.empty
        ):
            df_filteredPlus = column_functions.filter_DataStat(
                df_filtered_droped,
                gas=gas,
                column=column,
                clu_int=cluster_interval,
                drop_clu_info=version_ofDorp,
                clu_str=cluster_start,
                clu_end=cluster_end,
                clu_win=cluster_window,
                case=["outlier", "rollingMean"],  # , "continuous", "interval"],
            )
        else:
            df_filteredPlus = df_filtered_droped.drop(columns=["ID_Location"])

        # if gas == "xco2":
        #     print(df_filteredPlus)
        #     print(sorted(list(df_filteredPlus.columns)))

        # print(sorted(list(df_filtered.columns)))

        # if gas == "xco2":
        #     print(df_filtered_droped)
        #     print(df_filteredPlus)
        #     print(sorted(df_filtered_droped.columns))
        #     print(sorted(df_filteredPlus.columns))
        # df_filteredPlus = df_filtered_droped

        # Add Column ID_Location
        df_locationDay = (
            df_filtered[["ID_Location"]]
            .reset_index()
            .drop_duplicates(ignore_index=True)
            .set_index(["Date", "ID_Spectrometer"])
        )
        # print(df_locationDay)
        df_all_inf = df_filteredPlus.join(df_locationDay)
        ## airmass correction and removing useless columns -----------
        if gas == "xch4":
            df_corrected_inversion = column_functions.airmass_corr(
                df_all_inf, clc=True, big_dataSet=False
            )
            df_corrected_website = df_corrected_inversion.drop(
                [
                    "fvsi",
                    "sia_AU",
                    "asza_deg",
                    "xch4_ppm_sub_mean",
                    "xo2_error",
                    "pout_hPa",
                    "pins_mbar",
                    "elevation_angle",
                    "column_o2",
                    "column_h2o",
                    "column_air",
                    "xair",
                    "xh2o_ppm",
                ],
                axis=1,
            )
        else:
            df_corrected_inversion = df_all_inf
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

        # Website (raw + filtered)
        if case in ["website-raw", "website-filtered"]:
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

            df_corrected_inversion = df_corrected_inversion.drop(
                columns=["ID_Location", "Direction"]
            )

            columns_to_drop = [
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
                "column_h2o",
                "month",
                "year",
                "Date",
                "elevation_angle",
                "xch4_ppm_sub_mean",
            ]

            df_corrected_inversion = df_corrected_inversion.drop(
                columns=[
                    c for c in columns_to_drop if c in df_corrected_inversion.columns
                ]
            )

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

        merged_df.fillna("NaN").reset_index().rename(
            columns={"Hour": "year_day_hour"}
        ).set_index(["year_day_hour"]).to_csv(
            f"{project_dir}/data/csv-out-for-inversion/HAM{date_string}.csv"
        )

        def replace_from_dict(text):
            for key in replacement_dict:
                text = text.replace(f"%{key}%", str(replacement_dict[key]))
            return text

        with open(f"{project_dir}/data/inversion-header-template.csv", "r") as f:
            file_lines = list(map(replace_from_dict, f.readlines()))

        with open(
            f"{project_dir}/data/csv-out-for-inversion/HAM{date_string}.csv", "r"
        ) as f:
            file_lines += f.readlines()

        with open(
            f"{project_dir}/data/csv-out-for-inversion/HAM{date_string}.csv", "w"
        ) as f:
            for l in file_lines:
                f.write(l)

    else:
        return xco, xco2, xch4
    # maybe edn function here and give 3 dataframes as output

    # new functions for saving or uploading into DB after transforming it to json
    # =============================================================================
    #   Add code to save &/or upload csvs to database here
    #   read in while csv maybe not to efficient
    #   Maybe later groupby date convert to json
    # =============================================================================


def run(date_string):

    data_exists = False

    for case in ["website-raw", "website-filtered", "inversion-filtered"]:
        print(f"case = '{case}'")
        df_all, df_calibration, df_location, df_spectrometer = read_database(
            date_string, remove_calibration_data=(case == "inversion-filtered")
        )

        if not df_all.empty:
            df_calibrated, df_cali = column_functions.hp.calibration(
                df_all, df_calibration
            )

            df_calibration["ID"] = df_calibration["ID_SpectrometerCalibration"].map(
                lambda s: s[9:]
            )

            df_cali = df_calibration.replace([np.inf, np.nan], 21000101).replace(
                ["me17"], "me"
            )
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
                        count += 1
                    replacement_dict.update({f"CALIBRATION_{station}_{gas}": cal})
            if case == "inversion-filtered":
                filter_and_return(date_string, df_calibrated, df_location, case)
            else:
                xco, xco2, xch4 = filter_and_return(
                    date_string, df_calibrated, df_location, case
                )
                if case == "website-filtered":
                    xco2.round(5).to_csv(
                        f"{project_dir}/data/csv-in/{date_string}_co2.csv"
                    )
                    xch4.round(5).to_csv(
                        f"{project_dir}/data/csv-in/{date_string}_ch4.csv"
                    )
                if case == "website-raw":
                    xco2.round(5).to_csv(
                        f"{project_dir}/data/csv-in/{date_string}_co2_raw.csv"
                    )
                    xch4.round(5).to_csv(
                        f"{project_dir}/data/csv-in/{date_string}_ch4_raw.csv"
                    )
                data_exists = True

    if not data_exists:
        print("No new Data to Fetch yet")

    return data_exists
