import functools
import os
import json
from datetime import datetime, timezone


def unique(xs):
    return list(functools.reduce(lambda ys, y: ys if y in ys else ys+[y], xs, []))


def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)


def dump_json(path, document):
    with open(path, 'w') as f:
        json.dump(document, f)


def ls_ext(path, extension):
    """
    List the directory at the given path and only include the
    files with the given extension
    """
    return list(sorted([f for f in os.listdir(path) if f.endswith(extension)]))


def str_to_ts(timestring):
    dt = datetime.strptime(timestring, '%Y%m%d')
    return dt.replace(tzinfo=timezone.utc).timestamp()


def hour_to_ts(day_ts, hour):
    # Round to the nearest 10 seconds
    return round(day_ts + round(hour*3.6, 3) * 1000)


def concat(xss):
    return list(functools.reduce(lambda a, b: a+b, xss, []))
