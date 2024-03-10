from collections import namedtuple
from dataclasses import dataclass
from enum import Enum
import hashlib
import itertools
import re
from typing import Any, Dict, Iterable, Optional, List
import argparse


@dataclass
class Regex:
    patterns: List[re.Pattern]
    string: Optional[str]

    def __str__(self) -> str:
        if self.string:
            return self.string
        if self.patterns:
            return "|".join(self.patterns)
        else:
            return None

    def is_regex(self) -> bool:
        return any(self.patterns)

    @classmethod
    def from_string(cls, string: Optional[str]):
        if not string:
            return Regex([], None)
        patterns, string = [re.compile(c.replace("?", ".*")) for c in string.split(",") if "?" in string], None if "?" in string else string
        return Regex(patterns, string)

    def matches(self, string: str):
        if self.string:
            return self.string == string
        elif any(self.patterns):
            return any(p.fullmatch(string) for p in self.patterns)
        return True  # TODO: does it make sense? verify during tests


@dataclass
class Space:
    _dimension_number_to_regex: Dict[int, Regex]
    _everything: bool = False

    @classmethod
    def EVERYTHING(cls):
        return cls({}, True)

    @classmethod
    def from_list(cls, dims: List[str]):
        return Space({index: Regex.from_string(dim) for index, dim in enumerate(dims)})

    @classmethod
    def from_string(cls, string: str):
        if string == "?!":
            return cls.EVERYTHING()
        return Space.from_list(string.split("."))

    def get_dim_regex(self, index: int):
        return self._dimension_number_to_regex.get(index, None)

    def has(self, coordinates: List):
        if self._everything:
            return True
        for index, regex in self._dimension_number_to_regex.items():
            if len(coordinates) > index and not regex.matches(coordinates[index]):
                return False
        return True

@dataclass
class NodeLabel:
    module_name: str
    module: Any
    thing_type: str
    coordinates: List[str]

    def __str__(self):
        return f"{self.module_name}.{self.thing_type}@{'.'.join(self.coordinates)}"

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
    blob_filter: Regex
    id_filter: Regex


Result = namedtuple("Result", "id blob")


@dataclass
class Node:
    label: NodeLabel
    display: NodeDisplay
    results: Optional[List[Result]] = None


@dataclass
class Opts:
    _PARSER = None

    mod_to_space: Dict[str, Space]
    display_method: DisplayMethod
    blob_filter: Regex
    id_filter: Regex

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
        self.blob_filter = Regex.from_string(args.filter)
        self.id_filter = Regex.from_string(args.id_filter)

    def _iter_parsed_spaces(self, spaces: List[str]):
        discovered_keys = set()
        for space_kv in spaces:
            parts = space_kv.split("=")
            if len(parts) == 1:
                key, val = None, parts[0]
            if len(parts) == 2:
                key, val = parts
            else:
                raise Exception(f"Invalid space spec: {space_kv}! Must be k=s1[,s2,...] or s1[s2,...]")
            if key in discovered_keys:
                raise Exception(f"Invalid space spec, redefined space for {'module ' + key if key else 'all modules'}!")
            discovered_keys.add(key)
            yield key, Space.from_string(val)


@dataclass
class ThingBlueprint:
    module_name: str
    module: Any
    thing_type: Regex

    def __init__(self, available_modules, string: str):
        parts = string.split(".")
        if len(parts) == 0 or len(parts) > 2:
            raise Exception(f"Invalid node {string} - must be either [mod].[type|regex] or [type]")
        if len(parts) == 1:
            self.thing_type = Regex.from_string(parts[0])
            if self.thing_type.is_regex():
                raise Exception(f"Invalid node {string}. If you specify a regex for thing type, you must explictly provide a module!")
            self.module_name = self._find_module_for_type(available_modules, self.thing_type)
        else:
            self._module_name, self.thing_type = parts[0], Regex.from_string(parts[1])
            if self.module_name not in available_modules:
                raise Exception(f"Unsupported module {self.module_name}. Available ones are: {available_modules.keys()}") 
        self.module = available_modules[self.module_name]


    @staticmethod
    def _find_module_for_type(available_modules: Dict, tt: Regex) -> str:
        module_matches = set()
        for name, mod in available_modules.items():
            if any(tt.matches(mod_tt) for mod_tt in mod.thing_types()):
                module_matches.add(name)
        if len(module_matches) > 1:
            raise Exception(f"Ambiguous thing type {tt}, found in multiple modules: {module_matches}")
        if not module_matches:
            raise Exception(f"Cannot find thing type {tt} anywhere!")
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
            or Space.from_list(self.blueprint.module.default_coordinates())
        )
        concrete_types = [t for t in self.blueprint.module.thing_types() if self.blueprint.thing_type.matches(t)]
        concrete_coords = [coord for coord in self.blueprint.module.coordinates() if space.has(coord)]

        for ct, cc in itertools.product(concrete_types, concrete_coords):
            yield Node(
                    label=NodeLabel(
                        module_name = self.blueprint.module_name,
                        module = self.blueprint.module,
                        thing_type = ct,
                        coordinates = cc
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
    _REGEX = re.compile("(.*)\{(\d+)\}(.*)")

    negate: bool
    match_regex: Optional[re.Pattern]

    def __init__(self, negate: bool, regex: Optional[str]):
        self.negate = negate
        self.match_regex = self._parse_regex(regex)

    @classmethod
    def _parse_regex(cls, regex) -> Optional[re.Pattern]:
        if not regex:
            return None
        match_spec = cls._REGEX.match(regex)
        if not match_spec:
            raise Exception(f"Invalid link regex: {regex}. Must be in form \"[OPTIONAL_CHARS]{{REQUIRED_INT_LENGTH}}[OPTIONAL_CHARS]\"")
        return re.compile(f"{match_spec.group(1)}.{{{int(match_spec.group(2))}}}{match_spec.group(3)}")  # no overlaps here!

    def match(self, a: Result, b: Result) -> bool:
        if self.match_regex:
            a_match = self.match_regex.search(a.blob)
            if a_match and a_match.group() in b.blob:
                return not self.negate
            b_match = self.match_regex.search(b.blob)
            if b_match and b_match.group() in a.blob:
                return not self.negate
        else:
            result = a.id in b.blob or b.id in a.blob
            return not result if self.negate else result


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
