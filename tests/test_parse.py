import asyncio
import pytest
import re
from typing import Dict, List, Tuple

from overread.graph import Graph
from overread.model import DisplayMethod, Node, NodeDisplay, NodeLabel, LinkOpts
from overread.parse import parse

pytest_plugins = ('pytest_asyncio',)


_MATCH_ALL = re.compile(".*")


class DummyModule:
    @staticmethod
    def thing_types(): 
        return ("t1", "t2", "t3")

    @staticmethod
    async def places():
        for p1, p2 in [("a1", "b1"),("a1", "b2"),("a2", "b1"),("a2", "b2")]:
            yield p1, p2

    @staticmethod
    def default_place():
        return ("a1", "b1")


def _equals(actual: Graph[Node, LinkOpts], expected: Dict[str, Tuple[Node, List[Tuple[str, LinkOpts]]]]):
    visited = set()
    for n in actual.iter_all_nodes():
        if n.label.alias in visited:
            raise Exception(f"Duplicate node in actual graph: {n.label}")
        if n.label.alias not in expected:
            raise Exception(f"Unexpected node in actual graph: {n.label} not in {expected.keys()}")
        visited.add(n.label.alias)
        expected_node, expected_children_id_with_edge_attrs = expected[n.label.alias]
        if n != expected_node:
            raise Exception(f"Actual node {n} != {expected_node}")
        expected_children_id_with_edge_attrs = sorted(expected_children_id_with_edge_attrs, key=lambda x: x[0])
        children_id_with_edge_attrs = sorted([(c.label.alias, ea) for (c, ea) in actual.get_children_with_edge_attrs(n)], key=lambda x: x[0].label.alias)
        if expected_children_id_with_edge_attrs != children_id_with_edge_attrs:
            raise Exception(f"Children for node {n.label.alias} do not match")
    if expected.keys() != visited:
        raise Exception(f"Missing nodes in actual graph: {expected.keys()-visited}")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "input, expected, expected_error",
    [
        (
            "",
            {},
            False
        ),
        (
            "t1",
            {
                "a": (
                    Node(
                        label=NodeLabel(alias="a", module_name="dummy", module=DummyModule, thing_type="t1", place=("a1", "b1")), 
                        display=NodeDisplay(display_method=DisplayMethod.DEFAULT, content_filter=_MATCH_ALL, id_filter=_MATCH_ALL), 
                        results=None
                    ), []
                )
            },
            False
        ),
        (
            "t1 xx + t2 -s a2/b1 -f regex.* -i other_regex.* -v",
            {
                "xx": (
                    Node(
                        label=NodeLabel(alias="xx", module_name="dummy", module=DummyModule, thing_type="t1", place=("a1", "b1")), 
                        display=NodeDisplay(display_method=DisplayMethod.DEFAULT, content_filter=_MATCH_ALL, id_filter=_MATCH_ALL), 
                        results=None
                    ), []
                ),
                "b": (
                    Node(
                        label=NodeLabel(alias="b", module_name="dummy", module=DummyModule, thing_type="t2", place=("a2", "b1")), 
                        display=NodeDisplay(display_method=DisplayMethod.ALL, content_filter=re.compile("regex.*"), id_filter=re.compile("other_regex.*")), 
                        results=None
                    ), []
                )
            },
            False
        ),
        # (
        #     "t1 xx + t2 -s a*/b* -q",
        #     {
        #         "xx": (
        #             Node(
        #                 label=NodeLabel(alias="xx", module_name="dummy", module=DummyModule, thing_type="t1", place=("a1", "b1")), 
        #                 display=NodeDisplay(display_method=DisplayMethod.DEFAULT, content_filter=_MATCH_ALL, id_filter=_MATCH_ALL), 
        #                 results=None
        #             ), []
        #         ),
        #         "b": (
        #             Node(
        #                 label=NodeLabel(alias="b", module_name="dummy", module=DummyModule, thing_type="t2", place=("a2", "b1")), 
        #                 display=NodeDisplay(display_method=DisplayMethod.ALL, content_filter=_MATCH_ALL, id_filter=_MATCH_ALL), 
        #                 results=None
        #             ), []
        #         )
        #     },
        #     False
        # )
    ],
)
async def test_parse(input, expected: Dict[Node, List[Tuple[str, str, LinkOpts]]], expected_error: bool):
    args = input.split(" ") if input else []

    if expected_error:
        with pytest.raises(Exception):
            await parse(args, {"dummy": DummyModule})
    else:
        actual = await parse(args, {"dummy": DummyModule})
        _equals(actual, expected)
