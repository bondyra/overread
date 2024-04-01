from collections import namedtuple

from overread.graph import Graph


DummyNode = namedtuple("TestNode", ["name", "value"])
DummyEdgeAttrs = namedtuple("TestEdge", ["left", "right"])


def test_graph():
    nodes = {
        "a": DummyNode("a", 1),
        "b": DummyNode("b", 2),
        "c": DummyNode("c", 3),
        "c1": DummyNode("c", 3),
        "d": DummyNode("d", 4),
    }
    edges = {"a/b": DummyEdgeAttrs("a", "b"), "b/c": DummyEdgeAttrs("b", "c"), "a/c": DummyEdgeAttrs("a", "c")}

    g = Graph[DummyNode, DummyEdgeAttrs](
        list(nodes.values()), lambda n: n.name, [(e.left, e.right, e) for e in edges.values()]
    )

    assert g.get_root_ids() == ["a", "d"]
    assert list(g.get_children_with_edge_attrs(nodes["a"])) == [
        (nodes["b"], edges["a/b"]),
        (nodes["c"], edges["a/c"]),
        (nodes["c1"], edges["a/c"]),
    ]
    assert list(g.get_children_with_edge_attrs(nodes["b"])) == [(nodes["c"], edges["b/c"]), (nodes["c1"], edges["b/c"])]
    assert list(g.get_children_with_edge_attrs(nodes["c"])) == []
    assert list(g.get_children_with_edge_attrs(nodes["d"])) == []
    assert list(g.iter_nodes("a")) == [nodes["a"]]
    assert list(g.iter_nodes("c")) == [nodes["c"], nodes["c1"]]
    assert list(g.iter_all_nodes()) == list(nodes.values())
