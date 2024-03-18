from collections import namedtuple
from dataclasses import dataclass
from enum import Enum
import hashlib
import itertools
import re
from typing import Any, Dict, Iterable, Optional, List


@dataclass
class NodeLabel:
    alias: Optional[str]
    seq: Optional[str]
    module_name: str
    module: Any
    thing_type: str
    place: List[str]

    def display_type(self):
        return self.alias or f"{self.module_name}.{self.thing_type}"

    def display_place(self):
        return ".".join(self.place)

    def __str__(self):
        return f"{self.module_name}.{self.thing_type} ({'.'.join(self.place)})"

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
    seq: str
    alias: Optional[str]

    def generate(self, global_opts: GlobalOpts) -> Iterable[Node]:
        space = (
            self.opts.space
            or global_opts.mod_to_space.get(self.template.module_name)
            or global_opts.mod_to_space.get(None)
            or re.compile("_".join(self.template.module.default_place()))
        )
        concrete_types = [t for t in self.template.module.thing_types() if self.template.thing_type_pattern.match(t)]
        concrete_places = [place for place in self.template.module.places() if space.match("_".join(place))]

        for ct, cp in itertools.product(concrete_types, concrete_places):
            yield Node(
                label=NodeLabel(
                    alias=self.alias,
                    seq=self.seq,
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
                return (
                    None
                    if self.negate
                    else {"parent_id_in_child": parent_id_in_child, "child_id_in_parent": child_id_in_parent}
                )
            else:
                return {"id_match": False} if self.negate else None


@dataclass
class Link:
    left_seq: str
    right_seq: str
    link_opts: Optional[LinkOpts]
