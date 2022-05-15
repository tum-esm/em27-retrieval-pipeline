import pandas as pd
import numpy as np

from src import utils


def _calculate_y_prediction(x: float, a: float, b: float, c: float) -> float:
    return a * np.abs(x) ** 3 + b * np.abs(x) + c


def apply_airmass_correction(df: pd.DataFrame) -> pd.DataFrame:
    """
    Function to fit and correct 'xch4_ppm_sub_mean' values from air mass dependency
    :return:    Pandas DataFrame, corrected values are stored in column: 'xch4_ppm'
    """
    utils.functions.assert_df_columns(df, ["xch4_ppm", "asza_deg"])

    df = df.copy()
    df["elevation_angle"] = 90 - df["asza_deg"]
    df[f"xch4_ppm_sub_mean"] = df.sub(df[["xch4_ppm"]].groupby(level=[0, 1]).mean())[
        "xch4_ppm"
    ]

    # value shift to get not in trouble with devision thru zero
    df["tmp"] = df["xch4_ppm_sub_mean"] + 1

    # correction
    y_pred = _calculate_y_prediction(
        df["elevation_angle"].values,
        -5.39 * (10 ** -10),
        9.09 * (10 ** -5),
        9.97 * (10 ** -1),
    )
    y_real = df["tmp"].values
    df["xch4_ppm_sub_mean_corr"] = (y_real / y_pred) - 1
    df["xch4_ppm"] += df["xch4_ppm_sub_mean_corr"] - df["xch4_ppm_sub_mean"]

    return df.drop(
        ["tmp", "xch4_ppm_sub_mean_corr", "elevation_angle", "xch4_ppm_sub_mean"],
        axis=1,
    )
