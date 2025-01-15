import datetime as dt
import numpy as np
import math


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
