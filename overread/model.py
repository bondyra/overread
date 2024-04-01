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
        return f"{self.module_name}/{self.thing_type} [{self.alias}]"

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
        concrete_types = [t for t in self.template.module.thing_types() if self.template.thing_type_pattern.fullmatch(t)]
        concrete_places = [place async for place in self.template.module.places() if space.fullmatch("/".join(place))]

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
                    display_method=(
                        global_opts.display_method 
                        if global_opts.display_method != DisplayMethod.DEFAULT
                        else self.opts.display_method
                    ),
                    content_filter=self.opts.content_filter or global_opts.content_filter,
                    id_filter=self.opts.id_filter or global_opts.id_filter,
                ),
            )


Match = namedtuple("Match", "negate matches")


@dataclass
class LinkOpts:
    negate: bool
    text: Optional[str]

    def __init__(self, negate: bool, text: Optional[List]):
        self.negate = negate
        self.text = text

    def match(self, parent: Result, child: Result) -> Optional[Dict]:
        if self.text:
            match = self.text if self.text in parent.blob and self.text in child.blob else None
            if self.negate:
                return Match(negate=True, matches=[]) if not match else None
            return Match(negate=False, matches=[match]) if match else None
        else:
            matches = []
            if parent.id in child.blob:
                matches.append(parent.id)
            if child.id in parent.blob:
                matches.append(child.id)
            if self.negate:
                return Match(negate=True, matches=[]) if not matches else None
            return Match(negate=False, matches=matches) if matches else None


@dataclass
class Link:
    left_alias: str
    right_alias: str
    link_opts: Optional[LinkOpts]
