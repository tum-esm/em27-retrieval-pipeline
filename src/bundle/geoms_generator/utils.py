import datetime as dt
import glob
import os
import numpy as np
import math
import polars as pl
from src import bundle
from . import constants


def geoms_times_to_datetime(times: np.ndarray[float]) -> list[dt.datetime]:
    """Transforms GEOMS DATETIME variable to dt.datetime instances
    (input is seconds, since 1/1/2000 at 0UT)"""
    new_times: list[dt.datetime] = []
    times = times / 86400.0
    t_ref = dt.date(2000, 1, 1).toordinal()

    for t in times:
        t_tmp = dt.datetime.fromordinal(t_ref + int(t / 86400.0))
        t_del = dt.timedelta(days=(t - math.floor(t)))
        new_times.append(t_tmp + t_del)

    return new_times


def datetimes_to_geoms_times(times: list[dt.datetime]) -> list[float]:
    """Transforms dt.datetime instances to GEOMS DATETIME
    (output is seconds, since 1/1/2000 at 0UT)"""
    new_times: list[float] = []
    t_ref = np.longdouble(dt.date(2000, 1, 1).toordinal())
    for t in times:
        t_h = np.longdouble(t.hour)
        t_m = np.longdouble(t.minute)
        t_s = np.longdouble(t.second)
        t_ms = np.longdouble(t.microsecond)
        t_ord = np.longdouble(t.toordinal())
        gtime = t_ord + (t_h + (t_m + (t_s + t_ms / 1.0e6) / 60.0) / 60.0) / 24.0 - t_ref
        new_times.append(gtime * 86400.0)

    return new_times


def load_comb_invparms_df(results_folder: str, sensor_id: str) -> pl.DataFrame:
    df = bundle.load_results.load_results_directory(
        results_folder, sensor_id, parse_dc_timeseries=constants.PARSE_DC_TIMESERIES
    )

    # convert altim from m to km
    df = df.with_columns(pl.col("altim").div(1000).alias("altim"))

    # fill out of bounds values
    fill_value = -900_000
    for gas, max_value in [
        ("XCO2", 10_000),
        ("XCH4", 10),
        ("XCO", 10_000),
        ("XH2O", 10_000),
    ]:
        df = df.with_columns(
            pl.when(pl.col(gas).lt(0.0) | pl.col(gas).gt(max_value))
            .then(fill_value)
            .otherwise(pl.col(gas))
            .alias(gas)
        )

    # filter based on DC amplitude
    if constants.PARSE_DC_TIMESERIES:
        df = df.with_columns(
            pl.col("ch1_fwd_dc_mean")
            .add(pl.col("ch1_bwd_dc_mean"))
            .mul(0.5)
            .ge(0.05)
            .alias("ch1_valid"),
            pl.col("ch2_fwd_dc_mean")
            .add(pl.col("ch2_bwd_dc_mean"))
            .mul(0.5)
            .ge(0.01)
            .alias("ch2_valid"),
        )
        df = df.with_columns(
            pl.when("ch1_valid").then(pl.col("XCO2")).otherwise(fill_value).alias("XCO2"),
            pl.when("ch1_valid").then(pl.col("XCH4")).otherwise(fill_value).alias("XCH4"),
            pl.when("ch1_valid").then(pl.col("XH2O")).otherwise(fill_value).alias("XH2O"),
            pl.when("ch2_valid").then(pl.col("XCO")).otherwise(fill_value).alias("XCO"),
        )
        df = df.filter(pl.col("ch1_valid") | pl.col("ch2_valid"))
        df = df.drop("ch1_valid", "ch2_valid")

    # filter based on SZA and XAIR
    if constants.MIN_SZA is not None:
        df = df.filter(pl.col("appSZA").ge(constants.MIN_SZA))
    if constants.MIN_XAIR is not None:
        df = df.filter(pl.col("XAIR").ge(constants.MIN_XAIR))
    if constants.MAX_XAIR is not None:
        df = df.filter(pl.col("XAIR").le(constants.MAX_XAIR))

    return df


def get_ils_form_preprocess_inp(
    results_folder: str, date: dt.date
) -> tuple[float, float, float, float]:
    """Return ILS from preprocess input file."""
    search_path = os.path.join(
        results_folder, "input_files", f"preprocess*{date.strftime('%y%m%d')}.inp"
    )
    file_list = glob.glob(search_path)
    if len(file_list) == 0:
        return  # no parameters from ils present
    else:
        preprocess_input_file = file_list[0]

    with open(preprocess_input_file, "r") as f:
        lines = f.readlines()

    # go to second $ (counter i)
    # and read the following two lines (counter j)
    i = 0
    j = 0
    ils = []
    for line in lines:
        if line.startswith("$"):
            i += 1
            continue
        if i == 2:
            if j >= 2:
                break  # read only 2 lines
            tmp_ils = np.array(line.split(" ")).astype(float)
            ils.extend(tmp_ils)
            j += 1
    assert len(ils) == 4
    return (float(i) for i in ils)
