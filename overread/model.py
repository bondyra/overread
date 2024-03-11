from collections import namedtuple
from dataclasses import dataclass
from enum import Enum
import hashlib
import itertools
import re
from typing import Any, Dict, Iterable, Optional, List
import argparse


@dataclass
class NodeLabel:
    module_name: str
    module: Any
    thing_type: str
    place: List[str]

    def __str__(self):
        return f"{self.module_name}.{self.thing_type}@{'_'.join(self.place)}"

    def __hash__(self) -> int:
        h = hashlib.sha256(self.__str__().encode('utf-8'))
        return int(h.hexdigest(), 16)


class DisplayMethod(Enum):
    ALL=1
    DEFAULT=2
    MINIMAL=3


@dataclass
class NodeDisplay:
    seq: str
    display_method: DisplayMethod
    blob_filter: re.Pattern
    id_filter: re.Pattern


Result = namedtuple("Result", "id blob")


@dataclass
class Node:
    label: NodeLabel
    display: NodeDisplay
    results: Optional[List[Result]] = None


@dataclass
class Opts:
    _PARSER = None

    mod_to_space: Dict[str, re.Pattern]
    display_method: DisplayMethod
    blob_filter: re.Pattern
    id_filter: re.Pattern

    @classmethod
    def _add_arguments(cls, parser):
        parser.add_argument("--spaces", "-s", default="")
        parser.add_argument("--quiet", "-q", action="store_true")
        parser.add_argument("--verbose", "-v", action="store_true")
        parser.add_argument("--filter", "-f", default="")
        parser.add_argument("--id-filter", "-i", default="")

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        instance._PARSER = argparse.ArgumentParser()
        instance._add_arguments(instance._PARSER)
        return instance

    def __init__(self, part: List[str]) -> None:
        args = self._PARSER.parse_args(part)
        self.mod_to_space = dict(self._iter_parsed_spaces(args.spaces))
        self.display_method = DisplayMethod.ALL if args.verbose else DisplayMethod.MINIMAL if args.quiet else DisplayMethod.DEFAULT
        self.blob_filter = re.compile(args.filter or ".*")
        self.id_filter = re.compile(args.id_filter or ".*")

    def _iter_parsed_spaces(self, spaces: List[str]):
        discovered_keys = set()
        for space_kv in spaces:
            parts = space_kv.split("=")
            if len(parts) == 1:
                key, val = None, parts[0]
            if len(parts) == 2:
                key, val = parts
            else:
                raise Exception(f"Invalid space spec: {space_kv}! Must be MODULE=SPACE_REGEX or SPACE_REGEX")
            if key in discovered_keys:
                raise Exception(f"Invalid space spec, redefined space for {'module ' + key if key else 'all modules'}!")
            discovered_keys.add(key)
            yield key, re.compile(val or "")


@dataclass
class ThingBlueprint:
    module_name: str
    module: Any
    thing_type: re.Pattern

    def __init__(self, available_modules, string: str):
        parts = string.split(".")
        if len(parts) == 0 or len(parts) > 2:
            raise Exception(f"Invalid node {string} - must be either [mod].[type|regex] or [type]")
        if len(parts) == 1:
            self.thing_type = re.compile(parts[0])
            self.module_name = self._find_module(available_modules)
        else:
            self._module_name, self.thing_type = parts[0], re.compile(parts[1])
            if self.module_name not in available_modules:
                raise Exception(f"Unsupported module {self.module_name}. Available ones are: {available_modules.keys()}")
        self.module = available_modules[self.module_name]
        if not any(self.thing_type.match(mod_tt) for mod_tt in self.module.thing_types()):
            raise Exception(f"Thing type {self.module_name} does not have any matches in configured module: {self.module_name}!")

    def _find_module(self, available_modules: Dict) -> str:
        module_matches = set()
        for name, mod in available_modules.items():
            if any(self.thing_type.match(mod_tt) for mod_tt in mod.thing_types()):
                module_matches.add(name)
        if len(module_matches) > 1:
            raise Exception(f"Thing type {self.thing_type_literal} found in multiple modules: {module_matches}, can proceed only with one!")
        if not module_matches:
            raise Exception(f"Cannot find thing type {self.thing_type_literal} in any of the available modules: {available_modules.keys()}!")
        return module_matches.pop()


class NodeBlueprint:
    def __init__(self, seq: str, parts: List[str], available_modules: Dict[str, Any]):
        self.seq = seq
        self.blueprint = ThingBlueprint(available_modules, parts[0])
        self.opts = Opts(parts[1:])

    def inflate(self, default_opts: Opts) -> Iterable[Node]:
        space = (
            self.opts.mod_to_space.get(self.blueprint.module_name)
            or self.opts.mod_to_space.get(None)
            or default_opts.mod_to_space.get(self.blueprint.module_name)
            or default_opts.mod_to_space.get(None)
            or re.compile("_".join(self.blueprint.module.default_place()))
        )
        concrete_types = [t for t in self.blueprint.module.thing_types() if self.blueprint.thing_type.match(t)]
        concrete_places = [place for place in self.blueprint.module.places() if space.match("_".join(place))]

        for ct, cp in itertools.product(concrete_types, concrete_places):
            yield Node(
                    label=NodeLabel(
                        module_name = self.blueprint.module_name,
                        module = self.blueprint.module,
                        thing_type = ct,
                        place = cp
                    ),
                    display=NodeDisplay(
                        seq = self.seq,
                        display_method = self.opts.display_method or default_opts.display_method,
                        blob_filter = self.opts.blob_filter or default_opts.blob_filter,
                        id_filter = self.opts.id_filter or default_opts.id_filter
                    )
                )


@dataclass
class LinkOpts:
    negate: bool
    match_regex: Optional[re.Pattern]

    def __init__(self, negate: bool, regex: Optional[str]):
        self.negate = negate
        self.match_regex = re.compile(regex) if regex else None

    def match(self, parent: Result, child: Result) -> Optional[Dict]:
        if self.match_regex:
            parent_matches = [m for m in set(self.match_regex.findall(parent.blob)) if m in child.blob]
            if not self.negate and parent_matches:
                return {"child_has_parent_strings": parent_matches}
            child_matches = [m for m in set(self.match_regex.findall(child.blob)) if m in parent.blob]
            if child_matches:
                return None if self.negate else {"parent_has_child_strings": child_matches}
            return {"regex_match": False} if self.negate else None
        else:
            parent_id_in_child = parent.id in child.blob
            child_id_in_parent = child.id in parent.blob
            if parent_id_in_child or child_id_in_parent:
                return None if self.negate else {"parent_id_in_child": parent_id_in_child, "child_id_in_parent": child_id_in_parent}
            else:
                return {"id_match": False} if self.negate else None


@dataclass
class Link:
    left_seq: str
    right_seq: str
    link_opts: Optional[LinkOpts]

    @classmethod
    def from_part(self, part: str):
        link, *regex = part.split("_", 1)
        left_seq, right_seq, negate = self._parse_link(link)
        return Link(left_seq, right_seq, LinkOpts(negate, regex[0] if regex else None))

    @staticmethod
    def _parse_link(link):
        if "~" in link:
            negate = True
            left, right = link.split("~")
        elif "-" in link:
            negate = False
            left, right = link.split("-")
        else:
            raise Exception(f"Invalid link type: {link}")
        return left, right, negate
