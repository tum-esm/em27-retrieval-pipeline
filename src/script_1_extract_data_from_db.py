import numpy as np
import mysql.connector
import pandas as pd
import json
import datetime as datetime
import sys
import os
from src import column_functions

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


def read_database(date_string):
    db_connection = mysql.connector.connect(**config["mysql"])
    read = lambda sql_string: pd.read_sql(sql_string, con=db_connection)

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


def filter_and_return(df_calibrated, df_location, filter=True):
    ## Physical Filter ----------------------
    if filter:
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
            df_filtered_droped["xch4_ppm_sub_mean"] = df_filtered_droped.sub(
                df_filtered_droped[["xch4_ppm"]].groupby(level=[0, 1]).mean()
            )["xch4_ppm"]
        else:
            raise Exception

        ## Filter based on data statistics ----------------
        if filter:
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
            df_corrected = column_functions.airmass_corr(
                df_all_inf, clc=True, big_dataSet=False
            ).drop(
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
            df_corrected = df_all_inf.drop(
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

        df_corrected = (
            df_corrected.reset_index()
            .set_index(["ID_Location"])
            .join(df_location.set_index(["ID_Location"])[["Direction"]])
            .reset_index()
        )
        columns_to_drop = ["Date", "ID_Spectrometer", "Direction"]
        if filter:
            columns_to_drop += ["year", "month", "flag"]
            df_corrected.reset_index()
            df_corrected["Hour"] = df_corrected["Hour"].round(3)
        df_corrected.rename(
            columns={
                "Hour": "hour",
                "ID_Location": "location",
                "xco2_ppm": "x",
                "xch4_ppm": "x",
            },
            inplace=True,
        )
        df_corrected = df_corrected.drop(columns=columns_to_drop)
        df_corrected = df_corrected.set_index(["hour"]).sort_index()

        # RETURN FILTERED DATAFRAMES FOR FURTHER USE -NEXT FUNCTION  -> CONVERT TO JSON UPLOAD DB
        if gas == "xco":
            xco = df_corrected
        elif gas == "xco2":
            xco2 = df_corrected
        elif gas == "xch4":
            xch4 = df_corrected

    return xco, xco2, xch4

    # maybe edn function here and give 3 dataframes as output

    # new functions for saving or uploading into DB after transforming it to json
    # =============================================================================
    #   Add code to save &/or upload csvs to database here
    #   read in while csv maybe not to efficient
    #   Maybe later groupby date convert to json
    # =============================================================================


def run(date_string):
    # Read in Dataframe
    df_all, df_calibration, df_location, df_spectrometer = read_database(date_string)

    if not df_all.empty:
        df_calibrated, df_cali = column_functions.hp.calibration(df_all, df_calibration)

        xco, xco2, xch4 = filter_and_return(df_calibrated, df_location, filter=True)
        xco2.round(5).to_csv(f"{project_dir}/data/csv-in/{date_string}_co2.csv")
        xch4.round(5).to_csv(f"{project_dir}/data/csv-in/{date_string}_ch4.csv")

        xco, xco2, xch4 = filter_and_return(df_calibrated, df_location, filter=False)
        xco2.round(5).to_csv(f"{project_dir}/data/csv-in/{date_string}_co2_raw.csv")
        xch4.round(5).to_csv(f"{project_dir}/data/csv-in/{date_string}_ch4_raw.csv")
        return True

    else:
        print("No new Data to Fetch yet")
        return False
