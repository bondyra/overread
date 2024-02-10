import argparse
import asyncio
import importlib
from collections import namedtuple
from pprint import pprint
import sys


parser = argparse.ArgumentParser(prog="cesspool", description="dasdsad")
parser.add_argument("resource")
parser.add_argument("--group", "-g")


Input = namedtuple("Input", "plugin type_name group")
_plugins = {}


def plugin(name):
    if name not in _plugins:
        mod = importlib.import_module(name)
        _plugins[name] = mod
    return mod


def main():
    inp = list(_parse_args())[0]  # TODO
    el = asyncio.get_event_loop()
    mod.init()
    pprint(el.run_until_complete(mod.get(inp.group, inp.type_name)))


def _parse_args():
    for part in _iter_parts(sys.argv[1:]):
        args = parser.parse_args(part)
        plugin, type_name = args.resource.split(".")
        yield Input(plugin=plugin, type_name=type_name, group=tuple(args.group.split(".")))


def _iter_parts(args):
    current_part = []
    for a in args:
        if a == "--":
            yield current_part
        else:
            current_part.append(a)
    yield current_part
