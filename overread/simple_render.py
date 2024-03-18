from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

from overread.graph import Graph
from overread.model import DisplayMethod, LinkOpts, Node, Result

import yaml


@dataclass
class LinkedNode:
    node: Node
    link_opts: LinkOpts


@dataclass
class LinkContext:
    parent: Result
    link_opts: LinkOpts

    def match(self, result: Result) -> bool:
        return self.link_opts.match(self.parent, result)


def render(graph: Graph[Node, LinkOpts]):
    print(yaml.dump(dict(render_roots(graph))))


def render_roots(graph: Graph[Node, LinkOpts]) -> Iterable[Tuple[str, List]]:
    root_ids = graph.get_root_ids()
    for root_id in root_ids:
        nodes = graph.iter_nodes(root_id)
        for node in nodes:
            yield render_node(node, graph, None)


def render_node(node: Node, graph: Graph[Node, LinkOpts], parent_context: Optional[LinkContext]) -> Tuple[str, List]:
    matching_results = [
        r for r in node.results if node.display.content_filter.match(r.blob) and node.display.id_filter.match(r.blob)
    ]
    if parent_context:
        matching_results = [result for result in matching_results if parent_context.match(result)]
    child_linked_nodes = [LinkedNode(c, link_opts) for c, link_opts in graph.get_children_with_edge_attrs(node)]
    rendered_results = [render_result(r, graph, node, child_linked_nodes) for r in matching_results]
    return node.label.display_type(), [r for r in rendered_results if r]


def render_result(r: Result, graph: Graph[Node, LinkOpts], node: Node, child_linked_nodes: List[LinkedNode]) -> Dict:
    rendered_child_nodes = [render_node(cln.node, graph, LinkContext(r, cln.link_opts)) for cln in child_linked_nodes]
    return {
        r.id: {
            **render_result_content(r, node),
            **{k: v for (k, v) in rendered_child_nodes},
        }
    }


def render_result_content(result: Result, node: Node) -> Dict:
    if node.display.display_method == DisplayMethod.ALL:
        return {**result.content, "_in": node.label.display_place()}
    elif node.display.display_method == DisplayMethod.MINIMAL:
        return {"_in": node.label.display_place()}
    else:
        return {**node.label.module.prettify(node.label.thing_type, result.content), "_in": node.label.display_place()}
