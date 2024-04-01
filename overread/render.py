from typing import Dict, Iterable, List, Optional
import uuid

from overread.graph import Graph
from overread.model import DisplayMethod, LinkOpts, Match, Node
from collections import namedtuple


LinkedNode = namedtuple("LinkedNode", ["node", "link_opts"])
LinkContext = namedtuple("LinkContext", ["parent", "link_opts"])
ResultMatch = namedtuple("ResultMatch", ["result", "match"])

RenderedNode = namedtuple("RenderedNode", ["uuid", "meta", "results"])
RenderedMeta = namedtuple("RenderedMeta", ["id", "place", "color", "type", "negate", "match_text"])
RenderedResult = namedtuple("RenderedResult", ["id", "color", "match", "content", "child_nodes"])


def render(graph: Graph[Node, LinkOpts]):
    print_nodes(render_obj(graph))


def render_obj(graph: Graph[Node, LinkOpts]):
    return list(render_graph(graph))


def render_graph(graph: Graph[Node, LinkOpts]) -> Iterable[RenderedNode]:
    root_ids = graph.get_root_ids()
    for root_id in root_ids:
        nodes = graph.iter_nodes(root_id)
        for node in nodes:
            yield render_node(node, graph, None)


def render_node(node: Node, graph: Graph[Node, LinkOpts], ctx: Optional[LinkContext]) -> RenderedNode:
    results = (
        r for r in node.results if node.display.content_filter.search(r.blob) and node.display.id_filter.search(r.id)
    )
    child_linked_nodes = [LinkedNode(c, link_opts) for c, link_opts in graph.get_children_with_edge_attrs(node)]
    result_matches = (
        ResultMatch(result, ctx.link_opts.match(ctx.parent, result) if ctx else Match(False, ["root"]))
        for result in results
    )
    return RenderedNode(
        uuid=str(uuid.uuid4()),
        meta=RenderedMeta(
            id=node.label.id_string(),
            place=node.label.place_string(),
            color=node.label.module.color(),
            type="linked" if ctx and ctx.link_opts else "root",
            negate=ctx.link_opts.negate if ctx and ctx.link_opts else None,
            match_text=(
                ctx.link_opts.text if ctx and ctx.link_opts and ctx.link_opts.text else None
            ),
        ),
        results=[render_result(r, graph, node, child_linked_nodes) for r in result_matches if r.match],
    )


def render_result(
    rm: ResultMatch, graph: Graph[Node, LinkOpts], node: Node, child_nodes: List[LinkedNode]
) -> RenderedResult:
    return RenderedResult(
        id=rm.result.id,
        color=node.label.module.color(),
        match=rm.match,
        content=render_result_content(rm, node),
        child_nodes=[render_node(cln.node, graph, LinkContext(rm.result, cln.link_opts)) for cln in child_nodes],
    )


def render_result_content(rm: ResultMatch, node: Node) -> Dict:
    if node.display.display_method == DisplayMethod.ALL:
        return rm.result.content
    elif node.display.display_method == DisplayMethod.MINIMAL:
        return {}
    else:
        return node.label.module.prettify(node.label.thing_type, rm.result.content)


def print_nodes(nodes: List[RenderedNode], prefix=""):
    for i, n in enumerate(nodes):
        branch, new_prefix = (
            (_dim("┕━ "), "   ")
            if len(nodes) == 1
            else (
                (_dim("┗━ "), "   ")
                if i == len(nodes) - 1
                else (_dim("┢━ "), _dim("┃  ")) if i == 0 else (_dim("┣━ "), _dim("┃  "))
            )
        )
        if n.meta.type == "root":
            print(f"{prefix}{branch}{_colored(f'{n.meta.id}', C_BOLD, *n.meta.color)} {_dim(f'(in {n.meta.place})')}")
            if n.results:
                print_results(n.results, f"{prefix}{new_prefix}")
        elif n.meta.type == "linked":
            place = f"in {n.meta.place}"
            link = (
                'not' if n.meta.negate else '' + f'contains "{n.meta.match_text}"' if n.meta.match_text else 'by id'
            )
            nomatch, nomatch_color = (_colored(" <no match>", C_FG_RED, C_DIM), [C_DIM]) if not n.results else ("", [])
            print(
                f"{prefix}{branch}{_colored(n.meta.id, C_BOLD, *nomatch_color, *n.meta.color)} {_dim(f'({place}, {link})')}{nomatch}"
            )
            if n.results:
                print_results(n.results, f"{prefix}{new_prefix}")
        else:
            assert False


def print_results(results: List[RenderedResult], prefix=""):
    for i, r in enumerate(results):
        branch, new_prefix = (_dim("┗━ "), "   ") if i == len(results) - 1 else (_dim("┣━ "), _dim("┃  "))
        link = f"{'☒' if r.match.negate else '☑'} {','.join(r.match.matches)}"
        print(f"{prefix}{branch}{_colored(r.id, r.color)} {_dim(f'({link})')}")
        if r.content:
            print_content(r.content, f"{prefix}{new_prefix}", not r.child_nodes)
        print_nodes(r.child_nodes, f"{prefix}{new_prefix}")


def print_content(content: Dict, prefix, no_children):
    items = [(_dim("┐"), o) for o in content] if isinstance(content, list) else content.items()
    plain_items = [k for k, v in items if not isinstance(v, dict) and not isinstance(v, list)]
    max_key_len = max(len(p) for p in plain_items or [""])
    for i, (k, v) in enumerate(items):
        branch, new_prefix = (_dim("└─"), "  ") if i == len(items) - 1 and no_children else (_dim("├─"), _dim("│ "))
        if isinstance(v, dict) and not v:
            print(f"{prefix}{branch}{f'{k}': <{max_key_len}} {{}}")
        elif isinstance(v, dict) and v:
            print(f"{prefix}{branch}{f'{k}': <{max_key_len}}")
            print_content(v, f"{prefix}{new_prefix}", no_children)
        elif isinstance(v, list) and v:
            print(f"{prefix}{branch}{f'{k}': <{max_key_len}}")
            print_content(v, f"{prefix}{new_prefix}", no_children)
        elif isinstance(v, list) and not v:
            print(f"{prefix}{branch}{f'{k}': <{max_key_len}} []")
        else:
            print(f"{prefix}{branch}{k: <{max_key_len}}: {(v or '<nil>')}")


def _dim(s):
    return f"{C_DIM}{s}{C_RESET}"


def _colored(s, *colors):
    return f"{''.join(c for c in colors)}{s}{C_RESET}"


C_RESET = "\033[0m"
C_BOLD = "\033[01m"
C_DIM = "\033[02m"
C_UNDERLINE = "\033[04m"
C_FG_RED = "\033[31m"
