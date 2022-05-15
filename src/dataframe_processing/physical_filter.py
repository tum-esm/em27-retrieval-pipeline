import pandas as pd


def apply_physical_filter(
    df: pd.DataFrame,
    fvsi_threshold: float = 5,
    sia_threshold: float = 0.4,
    sza_threshold: float = 75,
    step_size: float = 0.1,
    o2_error: float = 0.0005,
    flag: bool = True,
) -> pd.DataFrame:
    if df.empty:
        return df

    """
    Function to filter on physical behavior. Based on Jias fitler approach.
    Input:
    :param data:        Pandas DataFrame, containing Data of one day and station
                            need columns: 'Hour', 'sia_AU', 'asza_deg', 'xo2_error', 'flag', 'fvsi'
    :param fvsi_threshold:  fractional variation in solar intensity < the value
    :param sia_threshold:   solar intensity average > value
    :param sza_threshold:   solar zenith angle < value
    :param step_size:
    :param o2_error:
    :param flag:        if false the flag parameter is not considered for filtering (except for no. 24 xair,
                        which shows an oversaturated signal); if 1, only measurements with flag <3 remain

    Output:
    :return: Pandas DataFrame, containing filtered values

    created by: Nico Nachtigall
    on: September 2020
    last modified: 20.10.2020
    """

    sia_ref = df[
        "sia_AU"
    ].values.copy()  # copy is needed here otherwise the values in the database are changed when sia_ref is modifyed
    time = df["Hour"].values

    # solar intensity reference values are calculated. Values have to be above those reference values
    m = sia_ref.max() * step_size
    for ii in range(0, sia_ref.size - 2):
        dt = time[ii + 1] - time[ii]
        if sia_ref[ii] - sia_ref[ii + 1] >= m * dt:
            sia_ref[ii + 1] = sia_ref[ii] - m * dt

    for ii in range(sia_ref.size - 1, 1, -1):
        dt = time[ii] - time[ii - 1]
        if sia_ref[ii] - sia_ref[ii - 1] >= m * dt:
            sia_ref[ii - 1] = sia_ref[ii] - m * dt

    # Filter step
    df = df.loc[
        (df["sia_AU"] >= sia_ref * sia_threshold)
        & (df["fvsi"] <= fvsi_threshold)
        & (df["asza_deg"] <= sza_threshold)
        & (df["xo2_error"] < o2_error)
    ]

    if flag:
        return df.loc[df["flag"] < 3]
    else:
        return df.loc[df["flag"] != 24]
