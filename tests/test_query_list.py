import pytest
from src import QueryList
from datetime import date
from typing import Any, Callable
from src.query_list import _Node


class TestQueryList:
    def _is_valid_query_list(self, query_list: Any) -> None:
        assert query_list._head._prev is None
        assert query_list._tail._next is None

        length = 1
        node: Any = query_list._head
        while node is not query_list._tail:
            assert node.end < node._next.start
            assert node._next._prev == node
            assert node.start <= node.end
            node = node._next
            length += 1

        assert len(query_list) == length

    def _is_query_list_expected(self, query_list: QueryList, expected: QueryList) -> None:
        assert query_list.slug == expected.slug
        assert len(query_list) == len(expected)
        for n, o in zip(query_list, expected):
            assert n.sensors == o.sensors and n.start == o.start and n.end == o.end

    @pytest.fixture
    def gen_query_list(self) -> Callable[[list[tuple[set[str], date, date]]], QueryList]:
        """Generates a query list from a list of tuples containing _Node information.

        gen_nodes = [
            ({sensors}, date(...), date(...)),
            ({sensors}, date(...), date(...)), ...]
        """

        def _gen_query_list(gen_nodes: list[tuple[set[str], date, date]]) -> QueryList:
            query_list = QueryList("")
            query_list._size = len(gen_nodes)
            sensors, start, end = gen_nodes[0]
            node = _Node(sensors, start, end, None, None)
            query_list._head = node
            for n in gen_nodes[1:]:
                sensors, start, end = n
                next_node = _Node(sensors, start, end, node, None)
                node._next = next_node
                node = next_node
            query_list._tail = node
            return query_list

        return _gen_query_list

    @pytest.fixture
    def gen_fix_query_list(self, gen_query_list: Any) -> Callable[[int, int], Any]:
        """Generates a query list with fix dates.

        gen_nodes = [
            ({""}, date(init_year + 0, 1, 1), date(init_year + 0, 2, 2)),
            ({""}, date(init_year + 1, 1, 1), date(init_year + 1, 2, 2)), ...]
        """

        def _gen_fix_query_list(init_year: int = 1, num_nodes: int = 1) -> Any:
            return gen_query_list(
                [
                    ({""}, date(i, 1, 1), date(i, 2, 2))
                    for i in range(init_year, init_year + num_nodes)
                ]
            )

        return _gen_fix_query_list

    def test_insert_no_overlap(self, gen_fix_query_list: Any) -> None:
        query_list = QueryList("")
        query_list.insert("", date(3, 1, 1), date(3, 2, 2))
        query_list.insert("", date(1, 1, 1), date(1, 2, 2))
        query_list.insert("", date(5, 1, 1), date(5, 2, 2))
        query_list.insert("", date(2, 1, 1), date(2, 2, 2))
        query_list.insert("", date(4, 1, 1), date(4, 2, 2))
        self._is_valid_query_list(query_list)
        expected = gen_fix_query_list(num_nodes=5)
        self._is_query_list_expected(query_list, expected)

    def test_insert_jointed_overlap(self, gen_query_list: Any) -> None:
        query_list = QueryList("")
        query_list.insert("S", date(1, 1, 10), date(1, 1, 20))
        query_list.insert("L", date(1, 1, 8), date(1, 1, 12))
        query_list.insert("R", date(1, 1, 18), date(1, 1, 22))
        query_list.insert("I", date(1, 1, 14), date(1, 1, 16))
        query_list.insert("O", date(1, 1, 6), date(1, 1, 24))
        query_list.insert("A", date(1, 1, 10), date(1, 1, 20))
        self._is_valid_query_list(query_list)
        # fmt: off
        expected = gen_query_list([
            ({"O"}, date(1, 1, 6), date(1, 1, 7)),
            ({"O","L"}, date(1, 1, 8), date(1, 1, 9)),
            ({"O","L","S","A"}, date(1, 1, 10), date(1, 1, 12)),
            ({"O","S","A"}, date(1, 1, 13), date(1, 1, 13)),
            ({"O","S","I","A"}, date(1, 1, 14), date(1, 1, 16)),
            ({"O","S","A"}, date(1, 1, 17), date(1, 1, 17)),
            ({"O","S","R","A"}, date(1, 1, 18), date(1, 1, 20)),
            ({"O","R"}, date(1, 1, 21), date(1, 1, 22)),
            ({"O"}, date(1, 1, 23), date(1, 1, 24)),
        ])
        # fmt: on
        self._is_query_list_expected(query_list, expected)

    def test_insert_disjointed_overlap(self, gen_query_list: Any) -> None:
        query_list = QueryList("")
        query_list.insert("K", date(1, 1, 3), date(1, 1, 6))
        query_list.insert("L", date(1, 1, 9), date(1, 1, 12))
        query_list.insert("R", date(1, 1, 15), date(1, 1, 18))
        query_list.insert("T", date(1, 1, 21), date(1, 1, 24))
        query_list.insert("I", date(1, 1, 11), date(1, 1, 16))
        query_list.insert("O", date(1, 1, 1), date(1, 1, 26))
        self._is_valid_query_list(query_list)
        # fmt: off
        expected = gen_query_list([
            ({"O"}, date(1, 1, 1), date(1, 1, 2)),
            ({"O", "K"}, date(1, 1, 3), date(1, 1, 6)),
            ({"O"}, date(1, 1, 7), date(1, 1, 8)),
            ({"O", "L"}, date(1, 1, 9), date(1, 1, 10)),
            ({"O", "L", "I"}, date(1, 1, 11), date(1, 1, 12)),
            ({"O", "I"}, date(1, 1, 13), date(1, 1, 14)),
            ({"O", "I", "R"}, date(1, 1, 15), date(1, 1, 16)),
            ({"O", "R"}, date(1, 1, 17), date(1, 1, 18)),
            ({"O"}, date(1, 1, 19), date(1, 1, 20)),
            ({"O", "T"}, date(1, 1, 21), date(1, 1, 24)),
            ({"O"}, date(1, 1, 25), date(1, 1, 26)),
            
        ])
        # fmt: on
        self._is_query_list_expected(query_list, expected)

    def test_optimize(self, gen_fix_query_list: Any) -> None:
        pass

    def test_filter(self, gen_fix_query_list: Any) -> None:
        pass

    def test_get_leftmost(self, gen_fix_query_list: Any) -> None:
        query_list = gen_fix_query_list(num_nodes=3, init_year=2)
        for start, expected in [
            (date(1, 1, 1), query_list._head),
            (date(2, 1, 1), query_list._head),
            (date(2, 2, 2), query_list._head),
            (date(2, 3, 1), query_list._head._next),
            (date(3, 1, 1), query_list._head._next),
            (date(3, 2, 2), query_list._head._next),
            (date(3, 3, 1), query_list._tail),
            (date(4, 1, 1), query_list._tail),
            (date(4, 2, 2), query_list._tail),
            (date(5, 1, 1), None),
        ]:
            assert query_list._get_leftmost(start) == expected

    def test_get_rightmost(self, gen_fix_query_list: Any) -> None:
        query_list = gen_fix_query_list(num_nodes=3, init_year=2)
        for start, expected in [
            (date(1, 1, 1), None),
            (date(2, 1, 1), query_list._head),
            (date(2, 2, 2), query_list._head),
            (date(2, 3, 1), query_list._head),
            (date(3, 1, 1), query_list._head._next),
            (date(3, 2, 2), query_list._head._next),
            (date(3, 3, 1), query_list._head._next),
            (date(4, 1, 1), query_list._tail),
            (date(4, 2, 2), query_list._tail),
            (date(5, 1, 1), query_list._tail),
        ]:
            assert query_list._get_rightmost(start) == expected

    def test_insert_left(self, gen_fix_query_list: Any) -> None:
        query_list = gen_fix_query_list(init_year=3)
        node = query_list._head
        query_list._insert_left(node, {""}, date(1, 1, 1), date(1, 2, 2))
        query_list._insert_left(node, {""}, date(2, 1, 1), date(2, 2, 2))
        self._is_valid_query_list(query_list)
        expected = gen_fix_query_list(num_nodes=3)
        self._is_query_list_expected(query_list, expected)

    def test_insert_right(self, gen_fix_query_list: Any) -> None:
        query_list = gen_fix_query_list(init_year=1)
        node = query_list._head
        query_list._insert_right(node, {""}, date(3, 1, 1), date(3, 2, 2))
        query_list._insert_right(node, {""}, date(2, 1, 1), date(2, 2, 2))
        self._is_valid_query_list(query_list)
        expected = gen_fix_query_list(num_nodes=3)
        self._is_query_list_expected(query_list, expected)

    def test_delete_to_left(self, gen_fix_query_list: Any) -> None:
        query_list = gen_fix_query_list(num_nodes=3)
        node = query_list._tail
        query_list._delete_to_left(node)
        query_list._delete_to_left(node)
        self._is_valid_query_list(query_list)
        expected = gen_fix_query_list(num_nodes=1, init_year=3)
        self._is_query_list_expected(query_list, expected)

    def test_delete_to_right(self, gen_fix_query_list: Any) -> None:
        query_list = gen_fix_query_list(num_nodes=3)
        node = query_list._head
        query_list._delete_to_right(node)
        query_list._delete_to_right(node)
        self._is_valid_query_list(query_list)
        expected = gen_fix_query_list(num_nodes=1)
        self._is_query_list_expected(query_list, expected)
