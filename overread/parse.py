import re
from typing import Dict, List, Tuple

from overread.graph import Graph
from overread.model import DisplayMethod, NodeOpts, NodeTemplate, ThingTemplate, GlobalOpts, LinkOpts, Node, Link
import argparse


GLOBALS_NODE_DIVIDER = "--"
NODE_DIVIDER = "+"
LINK_DIVIDER = "@"

DEFAULT_ALIASES = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n"]


async def parse(args: List[str], modules: Dict) -> Graph[Node, LinkOpts]:
    global_args, args = _split(args, GLOBALS_NODE_DIVIDER)
    global_opts = parse_global_opts(global_args)
    return await _parse_graph(args, global_opts, modules)


def _split(lst: List[str], divider: str) -> Tuple[List[str], List[str]]:
    if divider not in lst:
        return [], lst
    return lst[: lst.index(divider)], lst[(lst.index(divider) + 1) :]


async def _parse_graph(args, global_opts, modules):
    node_templates = []
    links = []

    def _parse_parts(state, parts):
        if state == NODE_DIVIDER:
            node_templates.append(parse_node_template(parts, modules, DEFAULT_ALIASES[len(node_templates)]))
        if state == LINK_DIVIDER:
            links.append(parse_link(parts))

    state = NODE_DIVIDER
    current_part = []

    for token in args:
        if token in {NODE_DIVIDER, LINK_DIVIDER}:
            _parse_parts(state, current_part)
            state = token
            current_part = []
        else:
            current_part.append(token)
    if current_part:
        _parse_parts(state, current_part)

    return Graph[Node, LinkOpts](
        [n for nt in node_templates async for n in nt.generate(global_opts)],
        lambda _: _.label.alias,
        [(l.left_alias, l.right_alias, l.link_opts) for l in links],
    )


global_opts_parser = argparse.ArgumentParser(prog="global")
global_opts_parser.add_argument("--mod-to-space", "-s", nargs="*")
global_opts_parser.add_argument("--quiet", "-q", action="store_true")
global_opts_parser.add_argument("--verbose", "-v", action="store_true")
global_opts_parser.add_argument("--filter", "-f", default="")
global_opts_parser.add_argument("--id-filter", "-i", default="")


def parse_global_opts(args: List[str]) -> GlobalOpts:
    args = global_opts_parser.parse_args(args)
    mod_to_space = dict(_iter_parse_spaces(args.mod_to_space)) if args.mod_to_space else {}
    display_method = (
        DisplayMethod.ALL if args.verbose else DisplayMethod.MINIMAL if args.quiet else DisplayMethod.DEFAULT
    )
    content_filter = re.compile(args.filter or ".*")
    id_filter = re.compile(args.id_filter or ".*")
    return GlobalOpts(mod_to_space, display_method, content_filter, id_filter)


def _iter_parse_spaces(mod_to_space: List[str]):
    discovered_keys = set()
    for space_kv in mod_to_space:
        parts = space_kv.split("=")
        if len(parts) == 1:
            key, val = None, parts[0]
        if len(parts) == 2:
            key, val = parts
        else:
            raise Exception(f"Invalid global mod-to-space spec: {space_kv}! Must be MODULE=SPACE_REGEX or SPACE_REGEX")
        if key in discovered_keys:
            raise Exception(
                f"Invalid global mod-to-space spec, redefined space for {'module ' + key if key else 'all modules'}!"
            )
        discovered_keys.add(key)
        yield key, re.compile(val or "")


node_parser = argparse.ArgumentParser(prog="node")
node_parser.add_argument("thing")
node_parser.add_argument("alias", nargs="?")
node_parser.add_argument("--space", "-s")
node_parser.add_argument("--quiet", "-q", action="store_true")
node_parser.add_argument("--verbose", "-v", action="store_true")
node_parser.add_argument("--filter", "-f", default="")
node_parser.add_argument("--id-filter", "-i", default="")
node_parser.add_argument("--transparent", "-t", action="store_true")


def parse_node_template(parts: List[str], modules: List[str], default_alias: str) -> NodeTemplate:
    args = node_parser.parse_args(parts)
    template = parse_thing_template(args.thing, modules)
    space = re.compile(args.space) if args.space else None
    display_method = (
        DisplayMethod.ALL if args.verbose else DisplayMethod.MINIMAL if args.quiet else DisplayMethod.DEFAULT
    )
    content_filter = re.compile(args.filter or ".*")
    id_filter = re.compile(args.id_filter or ".*")
    return NodeTemplate(
        alias=args.alias or default_alias,
        template=template,
        opts=NodeOpts(space, display_method, content_filter, id_filter, args.transparent),
    )


def parse_thing_template(string: str, available_modules) -> ThingTemplate:
    parts = string.split("_")
    if len(parts) == 0 or len(parts) > 2:
        raise Exception(f"Invalid node {string} - must be either [mod].[type_or_type_regex] or [type_or_type_regex]")
    if len(parts) == 1:
        thing_type_pattern = re.compile(parts[0])
        module_name = _find_module(thing_type_pattern, available_modules)
    else:
        module_name, thing_type_pattern = parts[0], re.compile(parts[1])
        if module_name not in available_modules:
            raise Exception(f"Unsupported module {module_name}. Available ones are: {available_modules.keys()}")
    module = available_modules[module_name]
    if not any(thing_type_pattern.match(mod_tt) for mod_tt in module.thing_types()):
        raise Exception(f"Thing type {module_name} does not have any matches in configured module: {module_name}!")
    return ThingTemplate(module_name, module, thing_type_pattern)


def _find_module(thing_type_pattern, available_modules: Dict) -> str:
    module_matches = set()
    for name, mod in available_modules.items():
        if any(thing_type_pattern.match(some_module_thing_type) for some_module_thing_type in mod.thing_types()):
            module_matches.add(name)
    if len(module_matches) > 1:
        # warning
        pass
    if not module_matches:
        raise Exception(f"Cannot find thing type {thing_type_pattern} in the modules: {available_modules.keys()}!")
    return module_matches.pop()


link_parser = argparse.ArgumentParser(prog="link")
link_parser.add_argument("link")
link_parser.add_argument("--regex", "-r")
link_parser.add_argument("--negate", "-n", action="store_true")


def parse_link(args: List[str]):
    args = link_parser.parse_args(args)
    if "/" not in args.link:
        raise Exception(f"Invalid link {args.link} - must be of form [parent]/[child]")
    left, right = args.link.split("/")
    return Link(left, right, LinkOpts(args.negate, re.compile(args.regex) if args.regex else None))
