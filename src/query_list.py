from __future__ import annotations

import os
from pathlib import Path
from attrs import define
from typing import Iterator, Any
from datetime import date, datetime, timedelta

PROJECT_DIR = Path(os.path.abspath(__file__)).parents[1]


@define(on_setattr=False)  # type: ignore
class _Node:
    sensors: set[str]
    start: date
    end: date
    _prev: _Node | None
    _next: _Node | None


class QueryList:

    """A doubly linked list that administers future requests for one location.

    Nodes are stored in an ordered manner and cover mutually exclusive dates.
    Each node is assigned to a start date, an end date as well as a sensor set.
    The set consists of all sensors requesting the data for the respective date range.
    """

    def __init__(self, coord: str) -> None:
        self.coord = coord
        self._head: _Node | None = None
        self._tail: _Node | None = None

    def __iter__(self) -> Iterator[_Node]:
        node = self._head
        while node is not None:
            yield node
            node = node._next

    def __str__(self) -> str:
        rep = []
        for i, n in enumerate(self):
            rep.append(f"({self.coord}-{i:03d}) {n.start} {n.end} {n.sensors}")
        return "\n".join(rep)

    def insert(self, sensor: str, start: date, end: date) -> None:

        """Insert a new node into the (ordered) query list.

        To insert a new node, this method uses the boundary nodes, i.e.,
        the outermost nodes that still overlap with the given start and end dates.
        The boundary nodes might get split in order to add the new sensor
        to an sub-interval of an already existing node. Inner nodes, i.e.,
        nodes in between the boundary nodes, are fully contained in the date range.
        Thus, their sensor set just needs to be extended by the new sensor.
        Finally, new nodes, with the sensor set just being the new sensor,
        are allocated to uncovered dates in between the boundary nodes.
        """

        if self._head is None:
            self._head = _Node({sensor}, start, end, None, None)
            self._tail = self._head
            return

        # Boundary nodes
        left = self._get_leftmost(start)
        right = self._get_rightmost(end)

        if right is None:
            # New node is leftmost node
            self._insert_left(self._head, {sensor}, start, end)
        elif left is None:
            # New node is rightmost node
            self._insert_right(self._tail, {sensor}, start, end)
        elif right.end < left.start:
            # New node only has non-overlapping neighbors
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

    def optimize(self, from_date: date | None, to_date: date) -> None:

        """Optimizes the query list.

        First, nodes with dates outside of the requested range are removed.
        Note that this step is necessary as node splitting during insertion might occur.
        Furthermore, dates that are already present in the output directory are excluded.
        In a second iteration, nodes with a time delta greater than 30 days are split
        and/or consecutive nodes that share the same sensor set are joined.
        """

        node: Any = self._head
        # Remove nodes to the left
        if from_date is not None:
            while node.end < from_date:
                node = node._next
                self._delete_to_left(node)
            node.start = from_date

        # Filter dates based on output directory
        while node is not self._tail and node._next.start <= to_date:
            self._filter(node)
            node = node._next

        # Remove nodes to the right
        if node is not self._tail:
            self._tail = node
            node._next = None
        node.end = to_date

        # Filter remaining node
        self._filter(node)

        node = self._head
        while node is not self._tail:
            # Split nodes a time delta > 30 days
            if (node.end - node.start).days > 30:
                self._insert_left(
                    node, node.sensors.copy(), node.start, node.start + timedelta(30)
                )
                node.start += timedelta(31)
            # Join consecutive nodes
            elif (
                node.end + timedelta(1) == node._next.start
                and node.sensors == node._next.sensors
            ):
                node.end = node._next.end
                self._delete_to_right(node)
            else:
                node = node._next

    def _filter(self, node: _Node) -> None:
        """Filters a node's dates based on the output directory."""

        split_date = None
        curr_date = node.start

        while curr_date <= node.end:

            path = f"{PROJECT_DIR}/vertical-profiles/{datetime.strftime(curr_date, '%Y%m%d')}_{self.coord}"  # FIXME -
            # Check if curr_date in output directory
            if os.path.isfile(f"{path}.map") and os.path.isfile(f"{path}.mod"):
                # All dates already present
                if node.start == node.end:
                    if self._head is self._tail:
                        self._head = None
                        self._tail = None
                    else:
                        self._delete_to_left(node._next)
                # Shift the start forward
                elif curr_date == node.start:
                    node.start += timedelta(1)
                # Shift the end backwards
                elif curr_date == node.end:
                    if split_date is None:
                        node.end -= timedelta(1)
                    else:
                        node.end = split_date
                    break
                # Mark an inner split position
                elif split_date is None:
                    split_date = curr_date - timedelta(1)

            # Split iff marked and curr_date not in output directory
            elif split_date is not None:
                self._insert_left(node, node.sensors.copy(), node.start, split_date)
                node.start = curr_date
                split_date = None

            curr_date += timedelta(1)

    def _get_leftmost(self, start: date) -> _Node | None:
        """Returns the first node from the left whose end date is not earlier than the given date."""
        node = self._head
        while node is not None and node.end < start:
            node = node._next
        return node

    def _get_rightmost(self, end: date) -> _Node | None:
        """Returns the first node from the right whose start date is not later than the given date."""
        node = self._tail
        while node is not None and end < node.start:
            node = node._prev
        return node

    def _insert_left(self, node: Any, sensors: set[str], start: date, end: date) -> None:
        """Inserts a new node to the left of the given node."""
        if node is self._head:
            node._prev = _Node(sensors, start, end, None, node)
            self._head = node._prev
        else:
            new_node = _Node(sensors, start, end, node._prev, node)
            node._prev._next = new_node
            node._prev = new_node

    def _insert_right(self, node: Any, sensors: set[str], start: date, end: date) -> None:
        """Inserts a new node to the right of the given node."""
        if node is self._tail:
            node._next = _Node(sensors, start, end, node, None)
            self._tail = node._next
        else:
            new_node = _Node(sensors, start, end, node, node._next)
            node._next._prev = new_node
            node._next = new_node

    def _delete_to_left(self, node: Any) -> None:
        """Deletes the node to the left of the given node."""
        if node._prev is self._head:
            self._head = node
            node._prev = None
        else:
            node._prev = node._prev._prev
            node._prev._next = node

    def _delete_to_right(self, node: Any) -> None:
        """Deletes the node to the right of the given node."""
        if node._next is self._tail:
            self._tail = node
            node._next = None
        else:
            node._next = node._next._next
            node._next._prev = node
