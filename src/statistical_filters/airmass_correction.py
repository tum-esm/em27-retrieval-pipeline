import pandas as pd
import numpy as np
import scipy


def _func(x: float, a: float, b: float, c: float) -> float:
    """
    fitting function for air mass correction
    called from correct()

    Input:
    :param x: elevation angle
    :param a: fitting parameter 1
    :param b: fitting parameter 2
    :param c: fitting parameter 3

    Output:
    :return: Number, calculated measurement

    created by: Nico Nachtigall
    on: September 2020
    last modified: 20.10.2020
    """

    return a * np.abs(x) ** 3 + b * np.abs(x) + c


def _correct(df_original: pd.DataFrame, calculation: bool = True) -> pd.DataFrame:
    """
    called from airmass_corr()
    Function to fit and correct 'xch4_ppm_sub_mean' values from air mass dependency

    Input:
    :param df_original: Pandas DataFrame, all measurements, needed column: 'xch4_ppm_sub_mean'
    :param calculation: Boolean, Ture if the parameter should be calculated, False if saved should be used

    Output:
    :return:            Pandas DataFrame, corrected values are stored in column: 'xch4_ppm_corr'

    created by: Nico Nachtigall
    on: September 2020
    last modified: 20.10.2020
    """
    # make copy to not change the original input DataFrame
    df = df_original.copy()

    # value shift to get not in trouble with devision thru zero
    df["xch4_ppm_sub_mean"] = df["xch4_ppm_sub_mean"] + 1

    # curve fitting -calculate values from big dataset
    if calculation:
        params, params_covariance = scipy.optimize.curve_fit(
            _func, df["elevation_angle"], df["xch4_ppm_sub_mean"]
        )
    else:
        # saved values when using small dataset
        params = [-5.39 * (10 ** -10), 9.09 * (10 ** -5), 9.97 * (10 ** -1)]

    # correction
    x = df["elevation_angle"].values
    y_pred = _func(x, params[0], params[1], params[2])
    y_real = df["xch4_ppm_sub_mean"].values
    df["xch4_ppm_sub_mean_corr"] = y_real / y_pred - 1

    # undo changes
    df["xch4_ppm_sub_mean"] = df["xch4_ppm_sub_mean"] - 1

    # correction of absolute measuremts
    df["mean"] = df["xch4_ppm"] - df["xch4_ppm_sub_mean"]
    df["xch4_ppm"] = df["mean"] + df["xch4_ppm_sub_mean_corr"]

    return df.drop(["mean", "xch4_ppm_sub_mean_corr"], axis=1)


def apply_airmass_correction(df: pd.DataFrame, calculate: bool = True) -> pd.DataFrame:
    """
    Function for air mass correction of measurements of methane
    Input:
    :param df:      Pandas DataFrame, containing all measurements,
                        columns needed: 'Hour', 'xch4_ppm_sub_mean', 'elevation_angle', 'xch4_ppm'
    :param kwargs:
        calculate:        True when new calculation is wished, false when literature parameter should be used

    Output:
    :return:        Pandas DataFrame, correced values are stored in columns: 'xch4_ppm_sub_mean_corr', 'xch4_ppm_corr'

    created by: Nico Nachtigall
    on: September 2020
    last modified: 20.10.2020
    """

    if calculate:
        df_corr = _correct(df, False)
    else:
        df_corr = df.copy()
        parameter = [-7.05 * (10 ** (-9)), 5.34 * (10 ** (-6)), 1.00059]
        x = df_corr["asza_deg"].values
        corr = _func(x, parameter[0], parameter[1], parameter[2])
        df_corr["xch4_ppm_corr"] = df_corr["xch4_ppm"] / corr
        df_corr["xch4_ppm"] = df_corr["xch4_ppm_corr"] - (
            df_corr["xch4_ppm"] - df_corr["xch4_ppm_sub_mean"]
        )
        df_corr = df_corr.drop(["xch4_ppm_corr"], axis=1)

    return df_corr
