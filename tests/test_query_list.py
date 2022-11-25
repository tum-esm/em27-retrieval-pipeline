import pytest
from datetime import date
from itertools import chain
from unittest.mock import patch
from typing import Any, Callable

from src.query_list import Query
from src import QueryList


class TestQueryList:
    @pytest.fixture
    def gen_query_list(self) -> Callable[[list[tuple[date, date, set[str]]]], QueryList]:
        """Generates a query list from a list of tuples containing _Node information.

        gen_nodes = [
            (date(...), date(...), {sensors}),
            (date(...), date(...), {sensors}), ...]
        """

        def _gen_query_list(gen_nodes: list[tuple[date, date, set[str]]]) -> QueryList:
            query_list = QueryList(0, 0)
            query_list._size = len(gen_nodes)
            start, end, sensors = gen_nodes[0]
            node = Query(start, end, sensors, None, None)
            query_list._head = node
            for n in gen_nodes[1:]:
                start, end, sensors = n
                next_node = Query(start, end, sensors, node, None)
                node._next = next_node
                node = next_node
            query_list._tail = node
            return query_list

        return _gen_query_list

    @pytest.fixture
    def gen_fix_query_list(self, gen_query_list: Any) -> Callable[[int, int], Any]:
        """Generates a query list with fix dates.

        gen_nodes = [
            (date(init_year + 0, 1, 1), date(init_year + 0, 2, 2), {""}),
            (date(init_year + 1, 1, 1), date(init_year + 1, 2, 2), {""}), ...]
        """

        def _gen_fix_query_list(init_year: int = 1, num_nodes: int = 1) -> Any:
            return gen_query_list(
                [
                    (date(i, 1, 1), date(i, 2, 2), {""})
                    for i in range(init_year, init_year + num_nodes)
                ]
            )

        return _gen_fix_query_list

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
        print(f"{query_list}\n{expected}")
        assert len(query_list) == len(expected)
        assert query_list.loc_str() == expected.loc_str()
        for n, o in zip(query_list, expected):
            assert n.sensors == o.sensors and n.start == o.start and n.end == o.end

    def test_insert_no_overlap(self, gen_fix_query_list: Any) -> None:
        query_list = QueryList(0, 0)
        query_list.insert(date(3, 1, 1), date(3, 2, 2), "")
        query_list.insert(date(1, 1, 1), date(1, 2, 2), "")
        query_list.insert(date(5, 1, 1), date(5, 2, 2), "")
        query_list.insert(date(2, 1, 1), date(2, 2, 2), "")
        query_list.insert(date(4, 1, 1), date(4, 2, 2), "")
        self._is_valid_query_list(query_list)
        expected = gen_fix_query_list(num_nodes=5)
        self._is_query_list_expected(query_list, expected)

    def test_insert_jointed_overlap(self, gen_query_list: Any) -> None:
        query_list = QueryList(0, 0)
        query_list.insert(date(1, 1, 10), date(1, 1, 20), "S")
        query_list.insert(date(1, 1, 8), date(1, 1, 12), "L")
        query_list.insert(date(1, 1, 18), date(1, 1, 22), "R")
        query_list.insert(date(1, 1, 14), date(1, 1, 16), "I")
        query_list.insert(date(1, 1, 6), date(1, 1, 24), "O")
        query_list.insert(date(1, 1, 10), date(1, 1, 20), "A")
        self._is_valid_query_list(query_list)
        # fmt: off
        expected = gen_query_list([
            (date(1, 1, 6), date(1, 1, 7), {"O"}),
            (date(1, 1, 8), date(1, 1, 9), {"O","L"}),
            (date(1, 1, 10), date(1, 1, 12), {"O","L","S","A"}),
            (date(1, 1, 13), date(1, 1, 13), {"O","S","A"}),
            (date(1, 1, 14), date(1, 1, 16), {"O","S","I","A"}),
            (date(1, 1, 17), date(1, 1, 17), {"O","S","A"}),
            (date(1, 1, 18), date(1, 1, 20), {"O","S","R","A"}),
            (date(1, 1, 21), date(1, 1, 22), {"O","R"}),
            (date(1, 1, 23), date(1, 1, 24), {"O"}),
        ])
        # fmt: on
        self._is_query_list_expected(query_list, expected)

    def test_insert_disjointed_overlap(self, gen_query_list: Any) -> None:
        query_list = QueryList(0, 0)
        query_list.insert(date(1, 1, 3), date(1, 1, 6), "K")
        query_list.insert(date(1, 1, 9), date(1, 1, 12), "L")
        query_list.insert(date(1, 1, 15), date(1, 1, 18), "R")
        query_list.insert(date(1, 1, 21), date(1, 1, 24), "T")
        query_list.insert(date(1, 1, 11), date(1, 1, 16), "I")
        query_list.insert(date(1, 1, 1), date(1, 1, 26), "O")
        self._is_valid_query_list(query_list)
        # fmt: off
        expected = gen_query_list([
            (date(1, 1, 1), date(1, 1, 2), {"O"}),
            (date(1, 1, 3), date(1, 1, 6), {"O", "K"}),
            (date(1, 1, 7), date(1, 1, 8), {"O"}),
            (date(1, 1, 9), date(1, 1, 10), {"O", "L"}),
            (date(1, 1, 11), date(1, 1, 12), {"O", "L", "I"}),
            (date(1, 1, 13), date(1, 1, 14), {"O", "I"}),
            (date(1, 1, 15), date(1, 1, 16), {"O", "I", "R"}),
            (date(1, 1, 17), date(1, 1, 18), {"O", "R"}),
            (date(1, 1, 19), date(1, 1, 20), {"O"}),
            (date(1, 1, 21), date(1, 1, 24), {"O", "T"}),
            (date(1, 1, 25), date(1, 1, 26), {"O"}),
            
        ])
        # fmt: on
        self._is_query_list_expected(query_list, expected)

    def test_insert_short_interval(self, gen_query_list: Any) -> None:
        query_list = QueryList(0, 0)
        query_list.insert(date(1, 1, 11), date(1, 1, 11), "H")
        query_list.insert(date(1, 1, 20), date(1, 1, 20), "U")
        query_list.insert(date(1, 1, 15), date(1, 1, 16), "I")
        query_list.insert(date(1, 1, 15), date(1, 1, 16), "I")
        query_list.insert(date(1, 1, 12), date(1, 1, 12), "J")
        query_list.insert(date(1, 1, 19), date(1, 1, 19), "Z")
        query_list.insert(date(1, 1, 14), date(1, 1, 14), "L")
        query_list.insert(date(1, 1, 17), date(1, 1, 17), "R")
        query_list.insert(date(1, 1, 13), date(1, 1, 13), "K")
        query_list.insert(date(1, 1, 18), date(1, 1, 18), "T")
        query_list.insert(date(1, 1, 10), date(1, 1, 21), "O")
        query_list.insert(date(1, 1, 14), date(1, 1, 15), "H")
        query_list.insert(date(1, 1, 16), date(1, 1, 17), "U")
        query_list.insert(date(1, 1, 14), date(1, 1, 17), "X")
        query_list.insert(date(1, 1, 15), date(1, 1, 16), "Y")
        self._is_valid_query_list(query_list)
        # fmt: off
        expected = gen_query_list([
            (date(1, 1, 10), date(1, 1, 10), {"O"}),
            (date(1, 1, 11), date(1, 1, 11), {"O", "H"}),
            (date(1, 1, 12), date(1, 1, 12), {"O", "J"}),
            (date(1, 1, 13), date(1, 1, 13), {"O", "K"}),
            (date(1, 1, 14), date(1, 1, 14), {"O", "L", "H", "X"}),
            (date(1, 1, 15), date(1, 1, 15), {"O", "H", "X", "Y", "I"}),
            (date(1, 1, 16), date(1, 1, 16), {"O", "U", "X", "Y", "I"}),
            (date(1, 1, 17), date(1, 1, 17), {"O", "R", "U", "X"}),
            (date(1, 1, 18), date(1, 1, 18), {"O", "T"}),
            (date(1, 1, 19), date(1, 1, 19), {"O", "Z"}),
            (date(1, 1, 20), date(1, 1, 20), {"O", "U"}),
            (date(1, 1, 21), date(1, 1, 21), {"O"}),
            
        ])
        # fmt: on
        self._is_query_list_expected(query_list, expected)

    # @patch("src.query_list.exists", {""})
    @patch("src.query_list.os.path")
    def test_filter(self, mock_path: Any, gen_query_list: Any) -> None:
        query_list = QueryList(0, 0)
        query_list.insert(date(1, 1, 1), date(1, 1, 10), "")
        is_present = (True, True, False, False, True, True, False, False, True, True)
        mock_path.isfile.side_effect = list(
            chain.from_iterable([2 * [x] if x else [x] for x in is_present])  # type: ignore
        )
        mock_path.isdir.side_effect = list(
            chain.from_iterable([3 * [x] for x in is_present if x])
        )
        query_list.filter("")
        self._is_valid_query_list(query_list)
        # fmt: off
        expected = gen_query_list([
            (date(1, 1, 3), date(1, 1, 4), {""}),
            (date(1, 1, 7), date(1, 1, 8), {""}),
        ])
        # fmt: on
        self._is_query_list_expected(query_list, expected)

    @patch("src.query_list.os.path")
    def test_filter_collapse(self, mock_path: Any, gen_query_list: Any) -> None:
        query_list = QueryList(0, 0)
        query_list.insert(date(1, 1, 1), date(1, 1, 1), "")
        query_list.insert(date(1, 1, 2), date(1, 1, 3), "")
        query_list.insert(date(1, 1, 4), date(1, 1, 4), "")
        is_present = (True, False, False, True)
        mock_path.isfile.side_effect = list(
            chain.from_iterable([2 * [x] if x else [x] for x in is_present])  # type: ignore
        )
        mock_path.isdir.side_effect = list(
            chain.from_iterable([3 * [x] for x in is_present if x])
        )
        query_list.filter("")
        self._is_valid_query_list(query_list)
        # fmt: off
        expected = gen_query_list([
            (date(1, 1, 2), date(1, 1, 3), {""}),
        ])
        # fmt: on
        self._is_query_list_expected(query_list, expected)
        mock_path.isfile.side_effect = 4 * [True]
        mock_path.isdir.side_effect = 6 * [True]
        query_list.filter("")
        assert len(query_list) == 0
        assert query_list._head == query_list._tail

    @patch("src.query_list.os.path")
    def test_filter_boundary(self, mock_path: Any, gen_query_list: Any) -> None:
        query_list = QueryList(0, 0)
        query_list.insert(date(1, 1, 1), date(1, 1, 4), "")
        query_list.insert(date(1, 1, 5), date(1, 1, 8), "")
        query_list.insert(date(1, 1, 9), date(1, 1, 12), "")
        # fmt: off
        is_present = (
            True, False, False, True,
            True, False, True, False,
            False, True, False, True
        )
        # fmt: on
        mock_path.isfile.side_effect = list(
            chain.from_iterable([2 * [x] if x else [x] for x in is_present])  # type: ignore
        )
        mock_path.isdir.side_effect = list(
            chain.from_iterable([3 * [x] for x in is_present if x])
        )
        query_list.filter("")
        self._is_valid_query_list(query_list)
        # fmt: off
        expected = gen_query_list([
            (date(1, 1, 2), date(1, 1, 3), {""}),
            (date(1, 1, 6), date(1, 1, 6), {""}),
            (date(1, 1, 8), date(1, 1, 8), {""}),
            (date(1, 1, 9), date(1, 1, 9), {""}),
            (date(1, 1, 11), date(1, 1, 11), {""}),
        ])
        # fmt: on
        self._is_query_list_expected(query_list, expected)

    def test_split_and_combine(self, gen_query_list: Any) -> None:
        query_list = QueryList(0, 0)
        query_list.insert(date(1, 7, 1), date(1, 7, 2), "A")
        query_list.insert(date(1, 7, 3), date(1, 9, 1), "A")
        query_list.insert(date(1, 9, 3), date(1, 9, 3), "A")
        query_list.insert(date(1, 9, 4), date(1, 9, 4), "A")
        query_list.insert(date(1, 9, 5), date(1, 9, 5), "B")
        query_list.insert(date(1, 10, 1), date(1, 10, 10), "B")
        query_list.insert(date(1, 10, 11), date(1, 10, 31), "B")
        query_list.split_and_combine()
        self._is_valid_query_list(query_list)
        # fmt: off
        expected = gen_query_list([
            (date(1, 7, 1), date(1, 7, 31), {"A"}),
            (date(1, 8, 1), date(1, 8, 31), {"A"}),
            (date(1, 9, 1), date(1, 9, 1), {"A"}),
            (date(1, 9, 3), date(1, 9, 4), {"A"}),
            (date(1, 9, 5), date(1, 9, 5), {"B"}) ,
            (date(1, 10, 1), date(1, 10, 31), {"B"})   
        ])
        # fmt: on
        self._is_query_list_expected(query_list, expected)

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
