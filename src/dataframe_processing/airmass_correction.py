import pandas as pd
import numpy as np

from src import utils


def _calculate_y_prediction(x: float, a: float, b: float, c: float) -> float:
    return a * np.abs(x) ** 3 + b * np.abs(x) + c


# TODO: Move calculation of "elevation_angle" and "xch4_ppm_sub_mean" in here because this
# is the only place where it is being used.
def apply_airmass_correction(df: pd.DataFrame) -> pd.DataFrame:
    """
    Function to fit and correct 'xch4_ppm_sub_mean' values from air mass dependency
    :return:    Pandas DataFrame, corrected values are stored in column: 'xch4_ppm'
    """
    assert utils.functions.is_subset_of(
        ["xch4_ppm_sub_mean", "elevation_angle", "xch4_ppm"],
        df.columns,
    )

    df = df.copy()

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

    # correction of absolute measuremts
    df["xch4_ppm"] += df["xch4_ppm_sub_mean_corr"] - df["xch4_ppm_sub_mean"]

    return df.drop(["tmp", "xch4_ppm_sub_mean_corr"], axis=1)
