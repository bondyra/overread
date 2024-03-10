
import json
from pprint import pprint
from typing import Dict, Iterable, List, Optional, Tuple

from overread.graph import Graph
from overread.model import DisplayMethod, LinkOpts, Node, Result


def render(graph: Graph[Node, LinkOpts]):
    pprint(dict(render_roots(graph)))


def render_roots(graph: Graph[Node, LinkOpts]) -> Iterable[Tuple[str, List]]:
    root_ids = graph.get_root_ids()
    for root_id in root_ids:
        nodes = graph.iter_nodes(root_id)
        for node in nodes:
            yield render_node(node, graph, None)


def render_node(node: Node, graph: Graph[Node, LinkOpts], parent_result_and_link_opts: Optional[Tuple[Result, LinkOpts]]) -> Tuple[str, List]:
    matching_results = [r for r in node.results if node.display.id_filter.matches(r.id)]
    matching_results = [r for r in matching_results if node.display.blob_filter.matches(r.blob)]
    if parent_result_and_link_opts:
        matching_results = [r for r in matching_results if parent_result_and_link_opts[1].match(parent_result_and_link_opts[0], r)]
    child_node_and_link_opts_items = [(cn, link_opts) for cid, link_opts in graph.get_children_id_and_edge(node.display.seq) for cn in graph.iter_nodes(cid)]
    rendered_results = [render_result(r, graph, node, child_node_and_link_opts_items) for r in matching_results]
    return str(node.label), [r for r in rendered_results if r]


def render_result(result: Result, graph: Graph[Node, LinkOpts], node: Node, child_node_and_link_opts_items: List[Tuple[Node, LinkOpts]]) -> Optional[Dict]:
    rendered_child_node_and_link_opts_items = [(render_node(cn, graph, (result, lo)), lo) for cn, lo in child_node_and_link_opts_items]
    return {
        result.id: {
            **render_result_blob(result, node),
            **{k: v for (k, v), _ in rendered_child_node_and_link_opts_items}
        }
    }


def render_result_blob(result: Result, node: Node) -> Dict:
    maybe_json = try_json(result.blob)
    if maybe_json:
        if node.display.display_method == DisplayMethod.DEFAULT:
            defaults = node.label.module.get_default_attrs(node.label.thing_type) or maybe_json.keys()
            return {k: maybe_json[k] for k in defaults}
        elif node.display.display_method == DisplayMethod.MINIMAL:
            return {}
        return maybe_json
    return {"blob": result.blob}


def try_json(blob):
    try:
        return json.loads(blob)
    except json.JSONDecodeError:
        return None
