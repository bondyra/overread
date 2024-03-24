from overread.execution import execute
from overread.modules import load_modules
from overread.render import render
from overread.parse import parse


async def get(args):
    modules = load_modules()
    graph = await parse(args, modules)
    await execute(graph)
    render(graph)
