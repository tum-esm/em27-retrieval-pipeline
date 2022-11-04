#!/usr/bin/env python
#  type: ignore

from typing import Callable
from datetime import date, timedelta
from attrs import field, define, Factory


@define(on_setattr=False)  # type: ignore
class Node:
    sensors: set[str]
    start: date
    end: date
    _prev: None  # Node | None
    _next: None  # Node | None


class QueryList:
    def __init__(self, coord: str, sensor: str, start: date, end: date) -> None:
        self.coord = coord
        node = Node({sensor}, start, end, None, None)
        self._head = node
        self._tail = node

    def __str__(self) -> str:
        index, rep, node = 1, [], self._head
        while node is not None:
            rep.append(f"({self.coord}-{index}) {node.start} {node.end} {node.sensors}")
            node = node._next
            index += 1
        return "\n".join(rep)

    def insert(self, sensor: str, start: date, end: date) -> None:

        left = self._get_leftmost(start)
        right = self._get_rightmost(end)

        if right is None:
            "|-In-||-Left-|..."
            self._insert_left(self._head, {sensor}, start, end)
        elif left is None:
            "...|-Right-||-In-|"
            self._insert_right(self._tail, {sensor}, start, end)
        elif right.end < left.start:
            "|-Right-||-In-||-Left-|"
            self._insert_right(right, {sensor}, start, end)
        else:

            if start < left.start:
                self._insert_left(left, {sensor}, start, left.start - timedelta(1))
            elif start > left.start and start <= left.end:
                self._insert_left(
                    left, left.sensors.copy(), left.start, start - timedelta(1)
                )
                left.start = start

            curr_node = left
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

            if end >= right.start and end < right.end:
                self._insert_right(
                    right, right.sensors.copy(), end + timedelta(1), right.end
                )
                right.end = end
            elif end > right.end:
                self._insert_right(right, {sensor}, right.end + timedelta(1), end)

            right.sensors.add(sensor)

    def optimize(self, from_date: date | None, to_date: date) -> None:

        # Adjust boundaries
        #if from_date is not None:
        #    print(self._head.start)
        #    self._head.start = from_date
        #self._tail.end = to_date

        # Adjust and filter #FIXME - 
        """ node = self._head
        while node is not self._tail:
            if node.end < from_date:
                node = node._next
                self._delete_to_left(node)
            elif node.start > to_date:
                node = node._next
                self._delete_to_left(node) """

        node = self._head
        # Collapse and split
        while node is not self._tail:
            if (node.end - node.start).days > 30:
                self._insert_left(
                    node, node.sensors.copy(),
                    node.start, node.start + timedelta(30)
                )
                node.start += timedelta(31)
            elif (
                node.end + timedelta(1) == node._next.start
                and node.sensors == node._next.sensors
            ):
                node.end = node._next.end
                self._delete_to_right(node)
            else:
                node = node._next

    def _get_leftmost(self, start: date) -> Node | None:
        node = self._head
        while node is not None and node.end < start:
            node = node._next
        return node

    def _get_rightmost(self, end: date) -> Node | None:
        node = self._tail
        while node is not None and end < node.start:
            node = node._prev
        return node

    def _insert_left(
        self, node: Node, sensors: set[str], start: date, end: date
    ) -> None:
        if node is self._head:
            node._prev = Node(sensors, start, end, None, node)
            self._head = node._prev
        else:
            new_node = Node(sensors, start, end, node._prev, node)
            node._prev._next = new_node
            node._prev = new_node

    def _insert_right(
        self, node: Node, sensors: set[str], start: date, end: date
    ) -> None:
        if node is self._tail:
            node._next = Node(sensors, start, end, node, None)
            self._tail = node._next
        else:
            new_node = Node(sensors, start, end, node, node._next)
            node._next._prev = new_node
            node._next = new_node

    def _delete_to_left(self, node: Node) -> None:
        if node._prev is self._head:
            self._head = node
            node._prev = None
        else:
            node._prev = node._prev._prev
            node._prev._next = node

    def _delete_to_right(self, node: Node) -> None:
        if node._next is self._tail:
            self._tail = node
            node._next = None
        else:
            node._next = node._next._next
            node._next._prev = node
