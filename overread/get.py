from overread.execution import execute
from overread.graph import Graph
from overread.model import Link, LinkOpts, Node, Opts, NodeBlueprint
from overread.modules import load_modules
from overread.default_render import render


def get(args):
    graph = get_graph(args)
    execute(graph)
    render(graph)


def get_graph(args):
    modules = load_modules()
    nonopt_start_index = _get_nonopt_start_index(args)
    default_opts = Opts(args[:nonopt_start_index])
    args = args[nonopt_start_index:]
    try:
        sep_index = args.index(":")
    except ValueError:
        node_parts, link_parts = args, []
    else:
        node_parts, link_parts = args[:sep_index], args[(sep_index+1):]
    node_blueprints = [NodeBlueprint(seq=str(seq+1), parts=parts, available_modules=modules) for seq, parts in enumerate(_iter_nodes(node_parts))]
    links = [Link.from_part(p) for p in link_parts]
    return Graph[Node, LinkOpts](
        [n for nb in node_blueprints for n in nb.inflate(default_opts)], 
        lambda _: _.display.seq, 
        [(l.left_seq, l.right_seq, l.link_opts) for l in links]
    )


def _get_nonopt_start_index(args):
    for index, arg in enumerate(args):
        if not arg.startswith("-"):
            return index
    return len(args)


def _iter_nodes(args):
    current_part = []
    for a in args:
        if a == "--":
            yield current_part
            current_part = []
        else:
            current_part.append(a)
    yield current_part
