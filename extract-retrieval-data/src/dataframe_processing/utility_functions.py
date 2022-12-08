"""
Project Description:
This program is part of the master thesis of Nico Nachtigall. It contains all functions, which are needed in addition to
the filter and background functions.

Author: Nico Nachtigall
created: September 2020
last modified: 20.10.2020
"""

import numpy as np
import pandas as pd


def cluster_by(
    df: pd.DataFrame,
    interval_max: float = None,
    interval_min: float = None,
    interval_delta: float = None,
    window_size: float = None,
    drop_clusterpoints_info: dict = {"drop": False, "version": "sigma", "percent": 0.2},
) -> pd.DataFrame:
    """
    Function to generate averaged measurements
    Averaging is always done with respect to day and site

    :param df:                      DataFrame
    :param interval_max:            Averaging end value
    :param interval_min:            Averaging start value
    :param interval_delta:          Step size of the rolling averaging window
    :param drop_clusterpoints_info: Dictionary, additional dropping information
                                    for cluster points
    :param window_size:             Averaging window size

    :return:                        DataFrame with averaged values, columns
                                    remain the same as df

    created by: Nico Nachtigall, September 2020
    last modified: 20.10.2020
    """

    # reset index and save original index
    index = df.index.names
    df = df.reset_index()
    key_to_cluster_by = "Hour"

    if interval_max is None:
        interval_max = df[key_to_cluster_by].max()
    if interval_min is None:
        interval_min = df[key_to_cluster_by].min()
    if interval_delta is None:
        interval_delta = (interval_max - interval_min) / 30
    if window_size is None:
        window_size = 2 * interval_delta

    assert window_size >= interval_delta

    win_add = (window_size - interval_delta) / 2 + interval_delta
    win_sub = (window_size - interval_delta) / 2

    # get steps
    steps = np.arange(interval_min, interval_max, interval_delta)

    # create empty data frame
    if np.isin(["ID_Location"], df.columns)[0]:
        df_clustered = pd.DataFrame(columns=np.append(df.columns, "count")).drop(
            ["ID_Location"], axis=1
        )
    else:
        df_clustered = pd.DataFrame(columns=np.append(df.columns, "count"))

    # different grouping schema, if columns 'ID_Spectrometer' and/or 'Date' are not present
    if (np.isin(["Date"], df.columns)[0]) & (
        np.isin(["ID_Spectrometer"], df.columns)[0]
    ):
        df = df.set_index(["Date", "ID_Spectrometer"])
        for s in steps:
            # get mean values over time
            df_temp = (
                df.loc[
                    (df[key_to_cluster_by] < (s + win_add))
                    & (df[key_to_cluster_by] >= (s - win_sub))
                ]
                .groupby(level=[0, 1])
                .mean()
                .reset_index()
            )
            df_temp["count"] = (
                df.loc[
                    (df[key_to_cluster_by] < (s + win_add))
                    & (df[key_to_cluster_by] >= (s - win_sub))
                ]
                .groupby(level=[0, 1])
                .count()
                .reset_index()[key_to_cluster_by]
            )
            # adjust some values
            df_temp[key_to_cluster_by] = s + (interval_delta / 2)
            df_clustered = df_clustered.append(df_temp, ignore_index=True)
        df_clustered["Date"] = df_clustered["Date"].astype(int)
        df_final = _get_month_year(df_clustered)

    elif np.isin(["ID_Spectrometer"], df.columns)[0]:
        df = df.set_index(["ID_Spectrometer"])
        for s in steps:
            # get mean values over time
            df_temp = (
                df.loc[
                    (df[key_to_cluster_by] < (s + win_add))
                    & (df[key_to_cluster_by] >= (s - win_sub))
                ]
                .groupby(level=[0])
                .mean()
                .reset_index()
            )
            df_temp["count"] = (
                df.loc[
                    (df[key_to_cluster_by] < (s + win_add))
                    & (df[key_to_cluster_by] >= (s - win_sub))
                ]
                .groupby(level=[0])
                .count()
                .reset_index()[key_to_cluster_by]
            )
            # adjust some values
            df_temp[key_to_cluster_by] = s + (interval_delta / 2)
            df_clustered = df_clustered.append(df_temp, ignore_index=True)
        df_final = df_clustered

    elif np.isin(["Date"], df.columns)[0]:
        df = df.set_index(["Date"])
        for s in steps:
            # get mean values over time
            df_temp = (
                df.loc[
                    (df[key_to_cluster_by] < (s + win_add))
                    & (df[key_to_cluster_by] >= (s - win_sub))
                ]
                .groupby(level=[0])
                .mean()
                .reset_index()
            )
            df_temp["count"] = (
                df.loc[
                    (df[key_to_cluster_by] < (s + win_add))
                    & (df[key_to_cluster_by] >= (s - win_sub))
                ]
                .groupby(level=[0])
                .count()
                .reset_index()[key_to_cluster_by]
            )
            # adjust some values
            df_temp[key_to_cluster_by] = s + (interval_delta / 2)
            df_clustered = df_clustered.append(df_temp, ignore_index=True)
        df_clustered["Date"] = df_clustered["Date"].astype(int)
        df_final = _get_month_year(df_clustered)
    else:
        for s in steps:
            # get mean values over time
            df_temp = (
                df.loc[
                    (df[key_to_cluster_by] < (s + win_add))
                    & (df[key_to_cluster_by] >= (s - win_sub))
                ]
                .mean()
                .reset_index()
            )
            df_temp["count"] = (
                df.loc[
                    (df[key_to_cluster_by] < (s + win_add))
                    & (df[key_to_cluster_by] >= (s - win_sub))
                ]
                .count()
                .reset_index()[key_to_cluster_by]
            )
            # adjust some values
            df_temp[key_to_cluster_by] = s + (interval_delta / 2)
            df_clustered = df_clustered.append(df_temp, ignore_index=True)
        df_clustered["Date"] = df_clustered["Date"].astype(int)
        df_final = _get_month_year(df_clustered)

    # remove all cluster Points which are calculated with too less data points
    if drop_clusterpoints_info["drop"]:
        df_final = _drop_cluster_points(
            df_final,
            drop_clusterpoints_info["version"],
            drop_clusterpoints_info["percent"],
        )
    # reindex with the old index
    return _set_index(df_final, index).drop("count", axis=1)


def timewindow_middle(
    np_timeseries, startPoint, time_interval_first, time_interval_sec
):
    # Function to return data window of interest
    # function is called from calculate_smooth_background()
    index = np.where(
        (np_timeseries >= startPoint - time_interval_first)
        & (np_timeseries < time_interval_sec + startPoint)
    )

    return np_timeseries[index], index[0]


def _drop_cluster_points(df, case, percent):
    """
    Function called from clusterby()
    Function to drop all rows where the averaged Point is not trustworthy
    this is defined by a threshold defining how many measurement Points are nessesary to trust the averaged Point
    the threshold is calculated based on a user defined percentage and either a given maximal information for an
    averaged measurement (in case of a small dataset) or by calculation of the maximal information (big dataset)
    :param df:      Pandas DataFrame, averaged measurements, need column 'count' (number of measurements per averaged point)
    :param case:    String: 'calculation' or Number: Maximal possible information for an averaged measurement
    :param percent: Number, [0,1]
    :return:        Pandas DataFrame, cleaned, same columns as df

    created by: Nico Nachtigall, September 2020
    last modified: 20.10.2020
    """

    if np.isin("count", df.columns, invert=True):
        print('Error dropping untrusted cluster points: "count" has to be a column')
        return df
    if case == "calculation":
        threshold = _get_threshold_untrusted_points(df, percent)
    else:
        threshold = case * percent
    return df[df["count"] > threshold]


def _get_threshold_untrusted_points(df, per):
    """
    Function is called by drop_ClusterPoints()
    Function returns a threshold with which the averaged measurement points are dropped
    :param df:  Pandas DataFrame, containing averaged measurements
    :param per: Number, [0,1] percentage how much information is necessary
    :return:    Number, threshold

    created by: Nico Nachtigall, September 2020
    last modified: 20.10.2020
    """
    if np.isin("count", df.columns, invert=True):
        print('"count" as to be in column')
        return 0

    np_count = df["count"].values
    return np.max(np_count) * per


def _get_month_year(df):
    """
    Function to calculate year and month
    :param df:  Pandas DataFrame, column needed: 'Date'
    :return:    Pandas DataFrame with additional columns: 'year' and 'month'

    created by: Nico Nachtigall, September 2020
    last modified: 20.10.2020
    """
    index = df.index
    df = df.reset_index()
    if np.isin(["Date"], df.columns)[0]:
        df["month"] = (
            df["Date"]
            .apply(lambda x: x - round(x, -4))
            .apply(lambda x: round(x, -2) / 100)
        )
        df["year"] = df["Date"].apply(lambda x: round(x / 10000))
    else:
        print('Column "date" is missing. No calculation possible.')

    df = _set_index(df, index)
    return df


def _set_index(df, column_array):
    """
    Helper function to set the index of the DataFrame to the columns stored in the input array
    :param df:              Pandas DataFrame
    :param column_array:    Numpy Array, containing column names of df which should be set as index
    :return:                Pandas DataFrame with chosen columns as index

    created by: Nico Nachtigall, September 2020
    last modified: 20.10.2020
    """
    try:
        if column_array[0] is None:
            return df
    except:
        return df
    df = df.set_index(column_array)
    if np.isin(["index"], df.columns)[0]:
        df_fin = df.drop(["index"], axis=1)
    elif np.isin(["index_0"], df.columns)[0]:
        df_fin = df.drop(["index_0"], axis=1)
    else:
        df_fin = df.copy()
    return df_fin