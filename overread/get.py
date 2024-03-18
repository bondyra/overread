from overread.execution import execute
from overread.modules import load_modules
from overread.simple_render import render
from overread.parse import parse_graph


def get(args):
    modules = load_modules()
    graph = parse_graph(args, modules)
    execute(graph)
    render(graph)
