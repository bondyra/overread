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


def _equals(actual: Graph[Node, LinkOpts], expected: Dict[str, List[Tuple[Node, List[Tuple[Node, LinkOpts]]]]]):
    visited_labels = set()
    for n in actual.iter_all_nodes():
        if n.label.alias not in expected:
            raise Exception(f"Unexpected node in actual graph: {n.label.alias} not in {expected.keys()}")
        visited_labels.add(n.label)
        expected_children_with_edges = [e for en, e in expected[n.label.alias] if en == n]
        if not expected_children_with_edges:
            raise Exception(f"{n} not in expected {expected[n.label.alias]}")
        if len(expected_children_with_edges) > 1:
            assert False, "Test setup error, two expected items are the same"
        expected_children_with_edges = expected_children_with_edges[0]
        expected_children_with_edges = sorted(expected_children_with_edges, key=lambda ve: str(ve[0]))
        actual_children_with_edges = sorted([(v.label, e) for (v, e) in actual.get_children_with_edge_attrs(n)], key=lambda ve: str(ve[0]))
        if expected_children_with_edges != actual_children_with_edges:
            raise Exception(f"Expected {expected_children_with_edges} != actual {actual_children_with_edges}")
    if sorted(map(str, {vv[0].label for v in expected.values() for vv in v})) != sorted(map(str, visited_labels)):
        raise Exception(f"Missing nodes in actual graph")


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
                "a": [(
                    Node(
                        label=NodeLabel(alias="a", module_name="dummy", module=DummyModule, thing_type="t1", place=("a1", "b1")), 
                        display=NodeDisplay(display_method=DisplayMethod.DEFAULT, content_filter=_MATCH_ALL, id_filter=_MATCH_ALL), 
                        results=None
                    ), []
                )]
            },
            False
        ),
        (
            "t1 xx + t2 -s a2/b1 -f regex.* -i other_regex.* -v",
            {
                "xx": [(
                    Node(
                        label=NodeLabel(alias="xx", module_name="dummy", module=DummyModule, thing_type="t1", place=("a1", "b1")), 
                        display=NodeDisplay(display_method=DisplayMethod.DEFAULT, content_filter=_MATCH_ALL, id_filter=_MATCH_ALL), 
                        results=None
                    ), []
                )],
                "b": [(
                    Node(
                        label=NodeLabel(alias="b", module_name="dummy", module=DummyModule, thing_type="t2", place=("a2", "b1")), 
                        display=NodeDisplay(display_method=DisplayMethod.ALL, content_filter=re.compile("regex.*"), id_filter=re.compile("other_regex.*")), 
                        results=None
                    ), []
                )]
            },
            False
        ),
        (
            "t1 xx + t2 -s a.*/b.* -q",
            {
                "xx": [(
                    Node(
                        label=NodeLabel(alias="xx", module_name="dummy", module=DummyModule, thing_type="t1", place=("a1", "b1")), 
                        display=NodeDisplay(display_method=DisplayMethod.DEFAULT, content_filter=_MATCH_ALL, id_filter=_MATCH_ALL), 
                        results=None
                    ), []
                )],
                "b": [
                    (
                    Node(
                        label=NodeLabel(alias="b", module_name="dummy", module=DummyModule, thing_type="t2", place=("a1", "b1")), 
                        display=NodeDisplay(display_method=DisplayMethod.MINIMAL, content_filter=_MATCH_ALL, id_filter=_MATCH_ALL), 
                        results=None
                    ), []
                    ),
                    (
                    Node(
                        label=NodeLabel(alias="b", module_name="dummy", module=DummyModule, thing_type="t2", place=("a2", "b1")), 
                        display=NodeDisplay(display_method=DisplayMethod.MINIMAL, content_filter=_MATCH_ALL, id_filter=_MATCH_ALL), 
                        results=None
                    ), []
                    ),
                    (
                    Node(
                        label=NodeLabel(alias="b", module_name="dummy", module=DummyModule, thing_type="t2", place=("a1", "b2")), 
                        display=NodeDisplay(display_method=DisplayMethod.MINIMAL, content_filter=_MATCH_ALL, id_filter=_MATCH_ALL), 
                        results=None
                    ), []
                    ),
                    (
                    Node(
                        label=NodeLabel(alias="b", module_name="dummy", module=DummyModule, thing_type="t2", place=("a2", "b2")), 
                        display=NodeDisplay(display_method=DisplayMethod.MINIMAL, content_filter=_MATCH_ALL, id_filter=_MATCH_ALL), 
                        results=None
                    ), []
                    )
                ]
            },
            False
        ),
        (
            "t1 + t2 yy -s a.*/b1 @ a/yy -n -r regex\\d{2}",
            {
                "a": [(
                    Node(
                        label=NodeLabel(alias="a", module_name="dummy", module=DummyModule, thing_type="t1", place=("a1", "b1")), 
                        display=NodeDisplay(display_method=DisplayMethod.DEFAULT, content_filter=_MATCH_ALL, id_filter=_MATCH_ALL), 
                        results=None
                    ), [
                        (
                            NodeLabel(alias="yy", module_name="dummy", module=DummyModule, thing_type="t2", place=("a1", "b1")), 
                            LinkOpts(negate=True, regex=re.compile("regex\\d{2}"))
                        ),
                        (
                            NodeLabel(alias="yy", module_name="dummy", module=DummyModule, thing_type="t2", place=("a2", "b1")), 
                            LinkOpts(negate=True, regex=re.compile("regex\\d{2}"))
                        )
                    ]
                )],
                "yy": [
                    (
                    Node(
                        label=NodeLabel(alias="yy", module_name="dummy", module=DummyModule, thing_type="t2", place=("a1", "b1")), 
                        display=NodeDisplay(display_method=DisplayMethod.DEFAULT, content_filter=_MATCH_ALL, id_filter=_MATCH_ALL), 
                        results=None
                    ), []
                    ),
                    (
                    Node(
                        label=NodeLabel(alias="yy", module_name="dummy", module=DummyModule, thing_type="t2", place=("a2", "b1")), 
                        display=NodeDisplay(display_method=DisplayMethod.DEFAULT, content_filter=_MATCH_ALL, id_filter=_MATCH_ALL), 
                        results=None
                    ), []
                    ),
                ]
            },
            False
        )
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
