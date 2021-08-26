import numpy as np
import mysql.connector
import pandas as pd

# import matplotlib.pyplot as plt
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
flag = 0

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


## Load data from Database --------------
# get connection to database
def read_database_from(Date, specific_day=False):
    mydb = mysql.connector.connect(
        host="10.195.1.241",
        user="user_basic",
        passwd="x32fsaF",
        database="ghg_measurements",
    )
    # get data from database
    if not specific_day:
        df_all = pd.read_sql(
            "SELECT * FROM measuredValues WHERE Date > " + str(Date), con=mydb
        )  # filter new stuff
    else:
        df_all = pd.read_sql(
            f"""
            SELECT *
            FROM measuredValues
            WHERE (Date = {Date}) AND
            ID_Location in ('TUM_I', 'FEL', 'OBE', 'TAU', 'GRÄ')
            AND ((NOT ID_Location = 'TUM_I') OR (ID_Spectrometer = 'ma61'))
            AND (NOT (ID_Spectrometer = 'mb86' AND ID_Location = 'TAU'))
            ORDER BY Hour
            """,
            con=mydb,
        )  # specific day
    # df_all = pd.read_sql('SELECT * FROM measuredValues', con=mydb) #filter all
    df_all.loc[df_all.Date <= 20170410, "xco_ppb"] = 0
    df_calibration = pd.read_sql(
        "SELECT * FROM spectrometerCalibrationFactor", con=mydb
    )
    df_location = pd.read_sql("SELECT * FROM location", con=mydb)
    df_spectrometer = pd.read_sql("SELECT * FROM spectrometer", con=mydb)
    # close connection to database
    mydb.close()
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


def filter_and_return(df_all, df_calibration, df_location, df_spectrometer):
    ## Data calibration ---------------------
    df_calibrated, df_cali = column_functions.hp.calibration(df_all, df_calibration)

    ## Color Definition for Plotting --------
    # df_color = column_functions.hp.create_colordf(df_spectrometer)

    ## Physical Filter ----------------------
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
    # df_filtered = df_calibrated.set_index(["Date", "ID_Spectrometer"])

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
        # df_filteredPlus = df_filtered_droped
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
                    "flag",
                    "xch4_ppm_sub_mean",
                    "xo2_error",
                    "pout_hPa",
                    "pins_mbar",
                    "elevation_angle",
                    "column_o2",
                    "column_h2o",
                    "column_air",
                    "xair",
                ],
                axis=1,
            )
        else:
            df_corrected = df_all_inf.drop(
                [
                    "fvsi",
                    "sia_AU",
                    "asza_deg",
                    "flag",
                    "xo2_error",
                    "pout_hPa",
                    "pins_mbar",
                    "column_o2",
                    "column_h2o",
                    "column_air",
                    "xair",
                ],
                axis=1,
            )

        df_corrected = (
            df_corrected.reset_index()
            .set_index(["ID_Location"])
            .join(df_location.set_index(["ID_Location"])[["Direction"]])
            .reset_index()
            .set_index(["Date", "Hour"])
            .sort_index()
        )
        df_corrected = Time_Stamp(df_corrected.reset_index())

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


def update_dataframe_for_website(date, path="data/website/", one_day=False):
    # Read in Dataframe
    df_all, df_calibration, df_location, df_spectrometer = read_database_from(
        str(date), specific_day=one_day
    )
    if not df_all.empty:
        xco, xco2, xch4 = filter_and_return(
            df_all, df_calibration, df_location, df_spectrometer
        )
        for day, df_day in xco2.groupby("Date"):
            df_day.round(5).to_csv(path + str(day) + "_xco2.csv")
        for day, df_day in xch4.groupby("Date"):
            df_day.round(5).to_csv(path + str(day) + "_xch4.csv")
        return True
    else:
        print("No new Data to Fetch yet")
        return False
