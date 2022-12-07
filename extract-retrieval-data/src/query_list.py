from __future__ import annotations

import os
#import shutil
from attrs import define
from pathlib import Path
from typing import Iterator, Any
from datetime import date, datetime, timedelta

from src.custom_types import StationId


@define
class Query:
    """A, e.g.,
    {
        station_set
    }.
    """

    from_date: date
    to_date: date
    station_set: set[StationId]
    _prev: Query | None
    _next: Query | None
    
    def __str__(self) -> str:
        return f"{self.from_date}-{self.to_date}; {self.station_set}"


class QueryList:

    """A doubly linked list that administers future postgres queries.
    Queries are stored in an ordered manner and cover mutually exclusive dates.
    """

    def __init__(self) -> None:
        self._head: Query | None = None
        self._tail: Query | None = None
        self._size: int = 0

    def __len__(self) -> int:
        return self._size

    def __iter__(self) -> Iterator[Query]:
        query = self._head
        while query is not None:
            yield query
            query = query._next
    
    def __str__(self) -> str:
        return "\n".join([f"({i:03d}) {q}" for i, q in enumerate(self)])

    def insert(self, from_date: date, to_date: date, sensor: StationId) -> None:

        """
        Inserts a new query into the query list.

        Works using boundary queries, i.e., the outermost queries that still
        overlap with the given from_date and to_date. The boundary queries
        might get split in order to add the new sensor to an sub-interval of
        an already existing query.

        Inner queries, i.e., queries in between the boundary queries, are fully
        contained in the date range. Thus, their station set just needs to be ex-
        tended by the new sensor. Finally, new queries are allocated to uncovered
        dates in between the boundary queries (station set = {sensor}).
        """

        if self._size == 0:
            self._head = Query(from_date, to_date, {sensor}, None, None)
            self._tail = self._head
            self._size += 1
            return

        left = self._get_leftmost(from_date)
        right = self._get_rightmost(to_date)

        if right is None:
            # Query is leftmost query
            self._insert_left(self._head, {sensor}, from_date, to_date)
        elif left is None:
            # Query is rightmost query
            self._insert_right(self._tail, {sensor}, from_date, to_date)
        elif right.to_date < left.from_date:
            # Query only has non-overlapping neighbors
            self._insert_right(right, {sensor}, from_date, to_date)
        else:
            # Process overlap with leftmost query
            if from_date < left.from_date:
                self._insert_left(left, {sensor}, from_date, left.from_date - timedelta(1))
            elif from_date > left.from_date and from_date <= left.to_date:
                self._insert_left(
                    left, left.station_set.copy(), left.from_date, from_date - timedelta(1)
                )
                left.from_date = from_date

            # Process inner queries
            curr_query: Any = left
            while curr_query is not right:
                curr_query.station_set.add(sensor)
                if curr_query.to_date + timedelta(1) < curr_query._next.from_date:
                    self._insert_right(
                        curr_query,
                        {sensor},
                        curr_query.to_date + timedelta(1),
                        curr_query._next.from_date - timedelta(1),
                    )
                    curr_query = curr_query._next
                curr_query = curr_query._next

            # Process overlap with rightmost query
            if to_date >= right.from_date and to_date < right.to_date:
                self._insert_right(
                    right, right.station_set.copy(), to_date + timedelta(1), right.to_date
                )
                right.to_date = to_date
            elif to_date > right.to_date:
                self._insert_right(right, {sensor}, right.to_date + timedelta(1), to_date)

            # Add sensor to remaining query
            right.station_set.add(sensor)

    def _get_leftmost(self, from_date: date) -> Query | None:
        """Returns the first query from the left whose to_date is not earlier than the given date."""
        query = self._head
        while query is not None and query.to_date < from_date:
            query = query._next
        return query

    def _get_rightmost(self, to_date: date) -> Query | None:
        """Returns the first query from the right whose from_date is not later than the given date."""
        query = self._tail
        while query is not None and to_date < query.from_date:
            query = query._prev
        return query

    def _insert_left(
        self, query: Any, sensors: set[str], from_date: date, to_date: date
    ) -> None:
        """Inserts a new query to the left of the given query."""
        if query is self._head:
            query._prev = Query(from_date, to_date, sensors, None, query)
            self._head = query._prev
        else:
            new_query = Query(from_date, to_date, sensors, query._prev, query)
            query._prev._next = new_query
            query._prev = new_query
        self._size += 1

    def _insert_right(
        self, query: Any, sensors: set[str], from_date: date, to_date: date
    ) -> None:
        """Inserts a new query to the right of the given query."""
        if query is self._tail:
            query._next = Query(from_date, to_date, sensors, query, None)
            self._tail = query._next
        else:
            new_query = Query(from_date, to_date, sensors, query, query._next)
            query._next._prev = new_query
            query._next = new_query
        self._size += 1

    def _delete_to_left(self, query: Any) -> None:
        """Deletes the query to the left of the given query."""
        if query._prev is self._head:
            self._head = query
            query._prev = None
        else:
            query._prev = query._prev._prev
            query._prev._next = query
        self._size -= 1

    def _delete_to_right(self, query: Any) -> None:
        """Deletes the query to the right of the given query."""
        if query._next is self._tail:
            self._tail = query
            query._next = None
        else:
            query._next = query._next._next
            query._next._prev = query
        self._size -= 1
