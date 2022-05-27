import json
import os
from datetime import datetime, timedelta

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))

with open(f"{PROJECT_DIR}/em27-location-data/data/sensors.json") as f:
    _LOCATION_DATA_SENSORS: dict = json.load(f)
with open(f"{PROJECT_DIR}/em27-location-data/data/locations.json") as f:
    _LOCATION_DATA_LOCATIONS: dict = json.load(f)

IGNORE_DATES_BEFORE = 20190913


def run():
    query_list = []
    for sensor in _LOCATION_DATA_SENSORS.keys():
        serial_number = _LOCATION_DATA_SENSORS[sensor]["serialNumber"]
        for time_period in _LOCATION_DATA_SENSORS[sensor]["locations"]:
            if time_period["to"] >= IGNORE_DATES_BEFORE:
                if time_period["from"] < IGNORE_DATES_BEFORE:
                    time_period["from"] = IGNORE_DATES_BEFORE
                coordinates = _get_coordinates(time_period["location"])
                query_list.append(
                    {
                        "sensor": sensor,
                        "serial_number": serial_number,
                        "from": time_period["from"],
                        "to": time_period["to"],
                        "lat": coordinates["lat"],
                        "lon": coordinates["lon"],
                        "location": time_period["location"],
                    }
                )
    return _optimize_query_list(query_list)


def _get_coordinates(location: str):
    try:
        c = _LOCATION_DATA_LOCATIONS[location]
        return {k: c[k] for k in ["lat", "lon", "alt"]}
    except KeyError:
        raise Exception(
            f'em27-location-data/data/locations.json is invalid, "{location}" not found'
        )


def _optimize_query_list(query_list):
    new_query_list_1 = []
    for query in query_list:
        new_query_list_1 += _split_query(query)

    new_query_list_2 = []
    for query in new_query_list_1:
        reduced_query = _reduce_query(query)
        if reduced_query is not None:
            new_query_list_2.append(reduced_query)

    return new_query_list_2


def _split_query(query):
    t1 = datetime.strptime(str(query["from"]), "%Y%m%d")
    t2 = datetime.strptime(str(query["to"]), "%Y%m%d")
    if (t2 - t1).days <= 30:
        return [query]
    else:
        query1 = json.loads(json.dumps(query))
        query2 = json.loads(json.dumps(query))
        query1["to"] = datetime.strftime(t1 + timedelta(days=30), "%Y%m%d")
        query2["from"] = datetime.strftime(t1 + timedelta(days=31), "%Y%m%d")
        return [query1] + _split_query(query2)


def _reduce_query(query):
    """
    Move the query["from"] date forward if date exists.
    Return None if all dates exist.
    """
    t1 = datetime.strptime(str(query["from"]), "%Y%m%d")
    t2 = datetime.strptime(str(query["to"]), "%Y%m%d")
    s = query["sensor"]
    sn = query["serial_number"]
    d = f"{PROJECT_DIR}/dataset/{s}{sn}/"

    while t1 <= t2:
        t_string = datetime.strftime(t1, "%Y%m%d")
        if not os.path.isfile(f"{d}/{s}{t_string}.map"):
            break
        if not os.path.isfile(f"{d}/{s}{t_string}.mod"):
            break
        t1 += timedelta(days=1)

    if t1 > t2:
        return None

    query["from"] = datetime.strftime(t1, "%Y%m%d")
    return query
