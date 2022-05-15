"""
Project Description:
This program is part of the master thesis of Nico Nachtigall. It contains all functions needed to filter the column
measurements.

Author: Nico Nachtigall
created: September 2020
last modified: 20.10.2020
"""


import numpy as np
import pandas as pd
import scipy
from src.dataframe_processing import utils


def _getIndexInterval(x, num, check_day=False):
    """
    Helper function for filter_intervall(df)
    Function return index values which should be deleted based on their interval size
    check_day = True, whole day is removed if an interval of size num does not exists
    check_day = False, intervals which do not contain num elements will be removed

    Input:
    :param x: numpy array
    :param num: number, interval size for which to check
    :param check_day: boolean, changes the behavior of the function

    Output:
    :return: numpy array, containing the index of all values, which should be removed

    created by: Nico Nachtigall
    on: September 2020
    last modified: 20.10.2020
    """

    np_int = np.diff(x) >= num
    # this if cause is called if a day is checked for continuous measurements, if one interval is found which satisfies
    # the conditions no points will be dropped
    if check_day:
        if np.where(np_int == True)[0].size != 0:
            return np.array([])
    np_indexBigGap = np.where(np_int == False)[0]
    np_badindex = np.array([])
    for i in np_indexBigGap:
        # check for end and if the next interval is valide
        if (i == np_indexBigGap[-1]) or (np.isin(i + 1, np_indexBigGap, invert=True)):
            np_badindex = np.append(np_badindex, np.arange(x[i], x[i + 1] + 1, 1))
        else:
            np_badindex = np.append(np_badindex, np.arange(x[i], x[i + 1], 1))
    return np_badindex


def _filter_interval(df, num, gap, check_day=False):
    """
    normally called by: filter_DataStat()
    Function to delete measuring intervals (which are defined as measurments between measuring gaps of time > 'gab')
    check_day = True, whole day is removed if an interval of size num does not exists
    check_day = False, intervals which do not contain num elements will be removed

    Input:
    :param df:          Pandas DataFrame, need columns: 'Date', 'ID_Spectrometer', 'Hour'
    :param num:         Number, interval size
    :param gap:         Number, time in second which defines a gap
    :param check_day:   Boolean

    Output:
    :return:            Pandas DataFrame, filtered Data

    created by: Nico Nachtigall
    on: September 2020
    last modified: 20.10.2020
    """

    df_reset = df.reset_index().drop(columns=["Date", "ID_Spectrometer"])
    np_diff = np.diff(
        df_reset["Hour"].values
    )  # get time difference between measurements
    np_indexGap = np.append(0, np.append((np.argwhere(np_diff > gap)), np_diff.size))
    np_indexToBeDroped = _getIndexInterval(
        np_indexGap, num, check_day
    )  # get index which measurements should be dropped
    return df_reset.drop(np_indexToBeDroped)


def _filter_day_alone(df):
    """
    normally called by: filter_DataStat()
    Function filters all days on which just one site was measuring
    Input:
    :param df: Pandas DataFrame, Measurements of one day, need Index to be 'Date', 'ID_Spectrometer'

    Output:
    :return: Pandas DataFrame

    created by: Nico Nachtigall
    on: September 2020
    last modified: 20.10.2020
    """

    if df.index.get_level_values(1).unique().values.shape[0] > 1:
        return df


def _zscore_move(df, column, interval, stepsize, threshold):
    """
    normally called by: filter_DataStat()
    Function to remove outliers
    for outliers detection a zscore algorithmus is used based on a rolling window

    Input:
    :param df:          Pandas DataFrame, containing measurements of one day and one station
    :param column:      String, label of the column which should be filtered
    :param interval:    Number, rolling window size in h
    :param stepsize:    Number, rolling window step in h
    :param threshold:   Number, zscore threshold above which the point is detected as outlier

    Output:
    :return:            Pandas DataFrame, where all outlier rows are removed, no index

    created by: Nico Nachtigall
    on: September 2020
    last modified: 20.10.2020
    """

    df_reset = df.reset_index().drop(columns=["Date", "ID_Spectrometer"])
    np_timexch4 = df_reset[["Hour", column]].values
    start_time = np_timexch4[:, 0].min()
    end_time = np_timexch4[:, 0].max()

    s = start_time

    np_storeDelete = np.array([])
    while s < end_time:  # rolling window

        # use full interval by default
        interval_first = interval / 2
        interval_secound = interval / 2
        # check full interval can be used
        if s < start_time + interval / 2:
            # calculate max possible interval
            interval_first = s - start_time
        if s > end_time - interval / 2:
            # calculate max possible interval
            interval_secound = end_time - s

        # get window
        time_w, index = utils.timewindow_middle(
            np_timexch4[:, 0], s, interval_first, interval_secound
        )

        # get values
        np_inter = np_timexch4[index, 1]

        # to make sure to have enough points for calculation, 100 is chosen randomly
        if len(np_inter) > 100:
            np_zscore = scipy.stats.zscore(np_inter)
            np_indexDelete = np.where(np.abs(np_zscore) > threshold)[0]

            np_storeDelete = np.append(np_storeDelete, time_w[np_indexDelete], axis=0)

        s = s + stepsize

    np_TimeDelete = np.unique(np_storeDelete)

    if len(np_TimeDelete) == 0:  # no outliers were detected
        return df_reset
    else:
        return df_reset.set_index("Hour").drop(np_TimeDelete).reset_index()


def filter_DataStat(
    df: pd.DataFrame,
    gas: str,
    cluster_output_step_size: float = 0.25,
    cluster_window_size: float = 0.5,
    cluster_start: float = None,
    cluster_end: float = None,
    drop_clusterpoints_info: dict = {
        "drop": False,
        "version": "sigma",
        "percent": 0.2,
    },
    filter_cases: list[str] = [
        "outlier",
        "interval",
        "rollingMean",
        "continuous",
        "singleDay",
    ],
):
    """
    Function to filter measurements based on data statistics
    with in this function the following filter are called:
      * Outlier filter
      * Interval filter
      * Average points to remove noise
      * delete measurement series if a site has measured too less Points per day in a row
      * delete all Points where just one site has measured

    Input:
    :param df:      Pandas DataFrame, containing all measurement data, index: 'Date', 'ID_Spectrometer'
    :param kwargs:  optional parameter
        clu_int:    Number, averaging interval, default: 0.25 [h]
        clu_drop:   Boolean, averaging point should be dropped if it consists of too less measurements, default: False
        clu_win:    Number, averaging window size, default: clu_int*2 [h]
        clu_str:    Number, time when the averaging should start each day, default: None [h]
        clu_end:    Number, time when the averaging should end, default: None [h]
        gas:        String, gas for which to filter ['xch4', 'xco2' or 'xco'], default: 'xch4'
        drop_clu_info:  Dictionary, containing the description of how to drop averaging points, similar to clu_drop
        case:       List, containing the filter steps which should be performed, just needed if not all steps should be
                    performed, can contain: 'outlier', 'interval', 'rollingMean', 'continuous', 'singleDay'

    Output:
    :return:        Pandas DataFrame, index 'Date', 'ID_Spectrometer'

    created by: Nico Nachtigall
    on: September 2020
    last modified: 20.10.2020
    """

    if gas == "xco":
        column = "xco_ppb"
    elif gas == "xco2":
        column = "xco2_ppm"
    elif gas == "xch4":
        column = "xch4_ppm"
    else:
        print('ERROR: No valid gas is set. Set gas to "xch4", "xco" or "xco2".')
    # Filter Outlier
    if "outlier" in filter_cases:
        df_filtered = (
            df.groupby(level=[0, 1])
            .apply(_zscore_move, column, 2, 1, 2.58)
            .reset_index(level=[2], drop=True)
        )
    else:
        df_filtered = df.copy()

    # filter interval
    if "interval" in filter_cases:
        df_filtered = (
            df_filtered.groupby(level=[0, 1])
            .apply(_filter_interval, 12, 0.005)
            .reset_index(level=2, drop=True)
        )

    # Average points to remove noise
    if "rollingMean" in filter_cases:
        df_filtered = utils.clusterby(
            df_filtered,
            "Hour",
            int_delta=cluster_output_step_size,
            drop_clu_info=drop_clusterpoints_info,
            int_max=cluster_end,
            int_min=cluster_start,
            win_size=cluster_window_size,
        ).sort_index()

    # filter all days with no 1h continous measurements: filter_intervall (function),
    #   1/clu_int (number of clusterpoints needed in an hour to have continuous measurements),
    #   clu_int+clu_int/2 (allowed gab size between two points, bigger than a normal gab but smaller than two)
    if "continuous" in filter_cases and "rollingMean" in filter_cases:
        df_filtered = df_filtered.groupby(["Date", "ID_Spectrometer"]).apply(
            _filter_interval,
            int(1 / cluster_output_step_size),
            1.5 * cluster_output_step_size,
            True,
        )
        try:
            df_filtered = df_filtered.reset_index(level=[2], drop=True)
        except:
            pass
    elif "continuous" in filter_cases:
        print(
            "Error: Continuous filter step could not be performed, rolling mean step is needed in addition! Filtering is canceled!"
        )
        return df_filtered

    # filter all days with just one site measuring
    if "singleDay" in filter_cases and "rollingMean" in filter_cases:
        df_filtered = df_filtered.groupby(["Date"], as_index=False).apply(
            _filter_day_alone
        )  # .reset_index(level=0,drop=True)
    elif "singleDay" in filter_cases:
        print(
            "Error: Single day filter step could not be performed, rolling mean step is needed in addition! Filtering is canceled!"
        )
        return df_filtered

    return df_filtered
