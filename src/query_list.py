from __future__ import annotations

import os
import shutil
from pathlib import Path
from attrs import define, field
from typing import Iterator, Any
from datetime import date, datetime, timedelta


@define
class Query:
    """A query represents a node within a QueryList.

    Assigned to a start date, an end date as well as a sensor set.
    The set consists of all sensors requesting the data for the date range.
    """

    start: date
    end: date
    sensors: set[str]
    _prev: Query | None
    _next: Query | None

    def __str__(self) -> str:
        return f"{self.start}-{self.end}; {self.sensors}"


class QueryList:

    """A doubly linked list that administers future queries for one location.
    Queries are stored in an ordered manner and cover mutually exclusive dates.
    """

    def __init__(self, lat: float, lon: float) -> None:
        self.lat = lat
        self.lon = lon
        self._head: Query | None = None
        self._tail: Query | None = None
        self._size: int = 0

    def __len__(self) -> int:
        return self._size

    def __iter__(self) -> Iterator[Query]:
        node = self._head
        while node is not None:
            yield node
            node = node._next

    def __str__(self) -> str:
        return "\n".join([f"({self.loc_str()}-{i:03d}) {q}" for i, q in enumerate(self)])

    def loc_str(self) -> str:
        return (
            str(abs(self.lat)).zfill(2)
            + ("S_" if self.lat < 0 else "N_")
            + str(abs(self.lon)).zfill(3)
            + ("W" if self.lon < 0 else "E")
        )

    def insert(self, start: date, end: date, sensor: str) -> None:

        """Inserts a new query (node) into the query list.

        Works using boundary nodes, i.e., the outermost nodes that
        still overlap with the given start and end dates. The boundary nodes
        might get split in order to add the new sensor to an sub-interval of
        an already existing node. Inner nodes, i.e., nodes in between the boundary
        nodes, are fully contained in the date range. Thus, their sensor set just
        needs to be extended by the new sensor. Finally, new nodes are allocated to
        uncovered dates in between the boundary nodes (sensor set = {sensor}).
        """

        if self._size == 0:
            self._head = Query(start, end, {sensor}, None, None)
            self._tail = self._head
            self._size += 1
            return

        left = self._get_leftmost(start)
        right = self._get_rightmost(end)

        if right is None:
            # Node is leftmost node
            self._insert_left(self._head, {sensor}, start, end)
        elif left is None:
            # Node is rightmost node
            self._insert_right(self._tail, {sensor}, start, end)
        elif right.end < left.start:
            # Node only has non-overlapping neighbors
            self._insert_right(right, {sensor}, start, end)
        else:
            # Process overlap with leftmost node
            if start < left.start:
                self._insert_left(left, {sensor}, start, left.start - timedelta(1))
            elif start > left.start and start <= left.end:
                self._insert_left(left, left.sensors.copy(), left.start, start - timedelta(1))
                left.start = start

            # Process inner nodes
            curr_node: Any = left
            while curr_node is not right:
                curr_node.sensors.add(sensor)
                if curr_node.end + timedelta(1) < curr_node._next.start:
                    self._insert_right(
                        curr_node,
                        {sensor},
                        curr_node.end + timedelta(1),
                        curr_node._next.start - timedelta(1),
                    )
                    curr_node = curr_node._next
                curr_node = curr_node._next

            # Process overlap with rightmost node
            if end >= right.start and end < right.end:
                self._insert_right(right, right.sensors.copy(), end + timedelta(1), right.end)
                right.end = end
            elif end > right.end:
                self._insert_right(right, {sensor}, right.end + timedelta(1), end)

            # Add sensor to remaining node
            right.sensors.add(sensor)

    def filter(self, dst_path: str) -> None:
        """Filters out query dates already present in dst_path."""
        node: Any = self._head
        while node is not None:

            split = None
            date = node.start
            while date <= node.end:

                name = f"{datetime.strftime(date, '%Y%m%d')}_{self.loc_str()}"

                exists = set()
                for sensor in node.sensors:
                    if (
                        os.path.isfile(f"{dst_path}/GGG2014/{sensor}/map/{name}.map")
                        and os.path.isfile(f"{dst_path}/GGG2014/{sensor}/mod/{name}.mod")
                        and os.path.isdir(f"{dst_path}/GGG2020/{sensor}/map/{name}")
                        and os.path.isdir(f"{dst_path}/GGG2020/{sensor}/mod/{name}")
                        and os.path.isdir(f"{dst_path}/GGG2020/{sensor}/vmr/{name}")
                    ):
                        exists.add(sensor)

                if exists:

                    if missing := node.sensors - exists:
                        exist = exists.pop()
                        for sensor in missing:
                            # FIXME - Remove old
                            shutil.copyfile(
                                f"{dst_path}/GGG2014/{exist}/map/{name}.map",
                                f"{dst_path}/GGG2014/{sensor}/map/{name}.map",
                            )
                            shutil.copyfile(
                                f"{dst_path}/GGG2014/{exist}/mod/{name}.mod",
                                f"{dst_path}/GGG2014/{sensor}/mod/{name}.mod",
                            )
                            shutil.copytree(
                                f"{dst_path}/GGG2020/{exist}/map/{name}",
                                f"{dst_path}/GGG2020/{sensor}/map/{name}",
                                dirs_exist_ok=True,
                            )
                            shutil.copytree(
                                f"{dst_path}/GGG2020/{exist}/mod/{name}",
                                f"{dst_path}/GGG2020/{sensor}/mod/{name}",
                                dirs_exist_ok=True,
                            )
                            shutil.copytree(
                                f"{dst_path}/GGG2020/{exist}/vmr/{name}",
                                f"{dst_path}/GGG2020/{sensor}/vmr/{name}",
                                dirs_exist_ok=True,
                            )

                    if node.start == node.end:
                        # Remove node
                        if self._size == 1:
                            self._head = None
                            self._tail = None
                            self._size = 0
                        elif node is self._head:
                            self._delete_to_left(node._next)
                        else:
                            self._delete_to_right(node._prev)

                    elif date == node.start:
                        # Shift start forward
                        node.start += timedelta(1)

                    elif date == node.end:
                        # Shift end backward
                        if split is None:
                            node.end -= timedelta(1)
                        else:
                            node.end = split

                    elif split is None:
                        # Mark inner split
                        split = date - timedelta(1)

                # Split if marked
                elif split is not None:
                    self._insert_left(node, node.sensors.copy(), node.start, split)
                    node.start = date
                    split = None

                date += timedelta(1)

            node = node._next

    def split_and_combine(self) -> None:
        """Split queries with time delta > 30 and combines consecutive nodes."""
        node: Any = self._head
        while node is not None:

            if (node.end - node.start).days > 30:
                # Split nodes
                self._insert_left(
                    node, node.sensors.copy(), node.start, node.start + timedelta(30)
                )
                node.start += timedelta(31)
            elif (
                node is not self._tail
                and node.sensors == node._next.sensors
                and node.end + timedelta(1) == node._next.start
            ):
                # Combine nodes
                node.end = node._next.end
                self._delete_to_right(node)
            else:
                node = node._next

    def _get_leftmost(self, start: date) -> Query | None:
        """Returns the first node from the left whose end date is not earlier than the given date."""
        node = self._head
        while node is not None and node.end < start:
            node = node._next
        return node

    def _get_rightmost(self, end: date) -> Query | None:
        """Returns the first node from the right whose start date is not later than the given date."""
        node = self._tail
        while node is not None and end < node.start:
            node = node._prev
        return node

    def _insert_left(self, node: Any, sensors: set[str], start: date, end: date) -> None:
        """Inserts a new node to the left of the given node."""
        if node is self._head:
            node._prev = Query(start, end, sensors, None, node)
            self._head = node._prev
        else:
            new_node = Query(start, end, sensors, node._prev, node)
            node._prev._next = new_node
            node._prev = new_node
        self._size += 1

    def _insert_right(self, node: Any, sensors: set[str], start: date, end: date) -> None:
        """Inserts a new node to the right of the given node."""
        if node is self._tail:
            node._next = Query(start, end, sensors, node, None)
            self._tail = node._next
        else:
            new_node = Query(start, end, sensors, node, node._next)
            node._next._prev = new_node
            node._next = new_node
        self._size += 1

    def _delete_to_left(self, node: Any) -> None:
        """Deletes the node to the left of the given node."""
        if node._prev is self._head:
            self._head = node
            node._prev = None
        else:
            node._prev = node._prev._prev
            node._prev._next = node
        self._size -= 1

    def _delete_to_right(self, node: Any) -> None:
        """Deletes the node to the right of the given node."""
        if node._next is self._tail:
            self._tail = node
            node._next = None
        else:
            node._next = node._next._next
            node._next._prev = node
        self._size -= 1
