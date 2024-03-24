from collections import namedtuple
from dataclasses import dataclass
from enum import Enum
import hashlib
import itertools
import re
from typing import Any, AsyncGenerator, Dict, Optional, List, Tuple


@dataclass
class NodeLabel:
    alias: str
    module_name: str
    module: Any
    thing_type: str
    place: Tuple[str]

    def id_string(self):
        return f"{self.module_name}.{self.thing_type} [{self.alias}]"

    def place_string(self):
        return "/".join(self.place)

    def __str__(self):
        return f"{self.module_name}.{self.thing_type} ({'#'.join(self.place)})"

    def __hash__(self) -> int:
        h = hashlib.sha256(self.__str__().encode("utf-8"))
        return int(h.hexdigest(), 16)


class DisplayMethod(Enum):
    ALL = 1
    DEFAULT = 2
    MINIMAL = 3


@dataclass
class NodeDisplay:
    display_method: DisplayMethod
    content_filter: re.Pattern
    id_filter: re.Pattern


Result = namedtuple("Result", "id content blob")


@dataclass
class Node:
    label: NodeLabel
    display: NodeDisplay
    results: Optional[List[Result]] = None


@dataclass
class GlobalOpts:
    mod_to_space: Dict[str, re.Pattern]
    display_method: DisplayMethod
    content_filter: re.Pattern
    id_filter: re.Pattern


@dataclass
class NodeOpts:
    space: Optional[re.Pattern]
    display_method: Optional[DisplayMethod]
    content_filter: Optional[re.Pattern]
    id_filter: Optional[re.Pattern]
    transparent: Optional[bool]


@dataclass
class ThingTemplate:
    module_name: str
    module: Any
    thing_type_pattern: re.Pattern


@dataclass
class NodeTemplate:
    template: ThingTemplate
    opts: NodeOpts
    alias: Optional[str]

    async def generate(self, global_opts: GlobalOpts) -> AsyncGenerator[Node, None]:
        space = (
            self.opts.space
            or global_opts.mod_to_space.get(self.template.module_name)
            or global_opts.mod_to_space.get(None)
            or re.compile("/".join(self.template.module.default_place()))
        )
        concrete_types = [t for t in self.template.module.thing_types() if self.template.thing_type_pattern.match(t)]
        concrete_places = [place async for place in self.template.module.places() if space.match("/".join(place))]

        for ct, cp in itertools.product(concrete_types, concrete_places):
            yield Node(
                label=NodeLabel(
                    alias=self.alias,
                    module_name=self.template.module_name,
                    module=self.template.module,
                    thing_type=ct,
                    place=cp,
                ),
                display=NodeDisplay(
                    display_method=self.opts.display_method or global_opts.display_method,
                    content_filter=self.opts.content_filter or global_opts.content_filter,
                    id_filter=self.opts.id_filter or global_opts.id_filter,
                ),
            )


Match = namedtuple("Match", "negate matches")


@dataclass
class LinkOpts:
    negate: bool
    match_regex: Optional[re.Pattern]

    def __init__(self, negate: bool, regex: Optional[List]):
        self.negate = negate
        self.match_regex = re.compile(regex) if regex else None

    def match(self, parent: Result, child: Result) -> Optional[Dict]:
        if self.match_regex:
            matches = [m for m in set(self.match_regex.findall(parent.blob)) if m in child.blob]
            if not self.negate and matches:
                return Match(negate=False, matches=matches)
            return Match(negate=True, matches=matches) if self.negate else None
        else:
            matches = []
            if parent.id in child.blob:
                matches.append(parent.id)
            if child.id in parent.blob:
                matches.append(child.id)
            if matches:
                return None if self.negate else Match(negate=False, matches=matches)
            else:
                return Match(negate=True, matches=matches) if self.negate else None


@dataclass
class Link:
    left_alias: str
    right_alias: str
    link_opts: Optional[LinkOpts]
