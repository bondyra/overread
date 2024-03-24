import pytest

from overread.parse import parse_graph, parse_global_opts, parse_link, parse_node_template, parse_thing_template


@pytest.mark.parametrize(
    "input,expected",
    [
        ("graph G { a -- b }", {"a": ["b"], "b": ["a"]}),
        ("graph G { a -- b -- c }", {"a": ["b", "c"], "b": ["a", "c"], "c": ["a", "b"]}),
        (
            "graph G { a -- b -- c -- d }",
            {"a": ["b", "c", "d"], "b": ["a", "c", "d"], "c": ["a", "b", "d"], "d": ["a", "b", "c"]},
        ),
    ],
)
def test_parse_graph():
    pass


def test_parse_global_opts():
    pass


def test_parse_node_template():
    pass


def test_parse_thing_template():
    pass


def test_parse_link():
    pass
