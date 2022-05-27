import os
from datetime import timedelta
from src.query import Query
from src.utils import TimeUtils, LocationData

dir = os.path.dirname
PROJECT_DIR = dir(dir(os.path.abspath(__file__)))

IGNORE_DATES_BEFORE = 201900101
IGNORE_DATES_AFTER = None

class QueryList:

    def __init__(self):
        self._list = QueryList._generate()
    
    def __iter__(self):
        for query in self._list:
            yield query

    def to_json(self):
        return [q.to_json() for q in self._list]
    
    def __len__(self):
        return len(self._list)

    @staticmethod
    def _generate() -> list[Query]:
        query_list = []
        for sensor in LocationData.sensor_names():
            for time_period in LocationData.get_location_list(sensor):
                location = time_period["location"]
                coordinates = LocationData.get_coordinates(location)
                query_list.append(
                    Query(
                        t_from_int=time_period["from"],
                        t_to_int=time_period["to"],
                        sensor=sensor,
                        serial_number=LocationData.get_serial_number(sensor),
                        lat=coordinates["lat"],
                        lon=coordinates["lon"],
                        location=location
                    )
                )
        return QueryList._optimize_query_list(query_list)

    @staticmethod
    def _optimize_query_list(query_list: list[Query]) -> list[Query]:
        new_query_list_1 = []
        for query in query_list:
            new_query_list_1 += QueryList._split_query(query)

        new_query_list_2 = []
        for query in new_query_list_1:
            reduced_query = QueryList._trim_query(query)
            if reduced_query is not None:
                new_query_list_2.append(reduced_query)

        return new_query_list_2


    @staticmethod
    def _split_query(query: Query) -> list[Query]:
        if (query.t_to_datetime - query.t_from_datetime).days <= 30:
            return [query]
        else:
            query.t_to_datetime = query.t_from_datetime + timedelta(days=30)
            query2 = query.clone()
            query2.t_from_datetime += timedelta(days=31)
            return [query] + QueryList._split_query(query2)


    @staticmethod
    def _trim_query(query: Query) -> Query:
        """
        Move the query["from"] date forward if date exists.
        Return None if all dates exist.
        """
        d = f"{PROJECT_DIR}/dataset/{query.sensor}{query.serial_number}/"

        t_exists = lambda t: (
            os.path.isfile(f"{d}/{query.sensor}{t}.map")
            and
            os.path.isfile(f"{d}/{query.sensor}{t}.mod")
        )

        while query.t_from_int <= query.t_to_int:
            if (IGNORE_DATES_BEFORE is not None) and (query.t_from_int < IGNORE_DATES_BEFORE):
                query.t_from_datetime += timedelta(days=1)
                continue
            if (IGNORE_DATES_AFTER is not None) and (query.t_to_int > IGNORE_DATES_AFTER):
                query.t_to_datetime -= timedelta(days=1)
                continue

            t1_exists = t_exists(query.t_from_str)
            t2_exists = t_exists(query.t_to_str)
            t2_is_too_recent = TimeUtils.delta_days_until_now(query.t_to_str) < 5

            if t1_exists:
                query.t_from_datetime += timedelta(days=1)
            if t2_exists or t2_is_too_recent:
                query.t_to_datetime -= timedelta(days=1)
            if not (t1_exists or t2_exists or t2_is_too_recent):
                break

        if query.t_from_int > query.t_to_int:
            return None

        return query
