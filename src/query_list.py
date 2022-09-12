from datetime import timedelta
from src.query import Query
from src.utils import TimeUtils, LocationData, load_setup
from src.utils.file_utils import FileUtils

PROJECT_DIR, CONFIG = load_setup(validate=False)

class QueryList:
    """
    This list contains instances of the Query class. Each generated instance
    spans accross at most 30 days. Only queries where no files have been generated
    yet are kept.
    """

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
        location_data = LocationData()

        query_list = []
        for sensor in location_data.sensor_names():
            for time_period in location_data.get_location_list(sensor):
                location = time_period["location"]
                coordinates = location_data.get_coordinates(location)
                query_list.append(
                    Query(
                        t_from_int=time_period["from"],
                        t_to_int=time_period["to"],
                        sensor=sensor,
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
            query1 = query.clone()
            query2 = query.clone()
            query1.t_to_datetime = query.t_from_datetime + timedelta(days=30)
            query2.t_from_datetime = query.t_from_datetime + timedelta(days=31)
            return [query1] + QueryList._split_query(query2)


    @staticmethod
    def _trim_query(query: Query) -> Query:
        """
        Move the query["from"] date forward if date exists.
        Move the query["to"] date backward if date exists or too recent
        Return None if all dates exist.
        """
        while query.t_from_int <= query.t_to_int:
            if (CONFIG["from"] is not None) and (query.t_from_int < CONFIG["from"]):
                query.t_from_datetime += timedelta(days=1)
                continue
            if (CONFIG["to"] is not None) and (query.t_to_int > CONFIG["to"]):
                query.t_to_datetime -= timedelta(days=1)
                continue

            changed = False
            if FileUtils.t_exists_in_dst(query.t_from_str, query):
                query.t_from_datetime += timedelta(days=1)
                changed = True
            if (
                FileUtils.t_exists_in_dst(query.t_to_str, query) or
                (TimeUtils.delta_days_until_now(query.t_to_str) < 5)
            ):
                query.t_to_datetime -= timedelta(days=1)
                changed = True

            if not changed:
                break

        if query.t_from_int > query.t_to_int:
            return None

        return query
