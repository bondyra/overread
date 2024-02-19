import argparse
from collections import namedtuple
from dataclasses import dataclass
from enum import Enum
import glob
import importlib
import itertools
import os
import re
import sys
from typing import Tuple, Union


_parser = argparse.ArgumentParser(prog="cesspool", description="dasdsad")
_parser.add_argument("something")
_parser.add_argument("--dimensions", "-d", default=[])
_parser.add_argument("--minimal", "-m", action="store_true")
_parser.add_argument("--all", "-a", action="store_true")
_parser.add_argument("--filter", "-f")  # TODO


Input = namedtuple("Input", "seq module_name module type dimensions display_method")


@dataclass
class StringOrPattern:
    val: Union[str, re.Pattern]

    @classmethod
    def from_string(cls, s):
        val = s
        if "?" in s:
            val = val.replace("?", ".*")
            return cls(re.compile(val))
        return cls(val)

    def matches(self, val):
        return self.val == val if isinstance(self.val, str) else self.val.fullmatch(val)


@dataclass
class Vector:
    vals: StringOrPattern

    @classmethod
    def from_tuple(cls, dims: Tuple[str]):
        return cls([StringOrPattern.from_string(dim) for dim in dims])

    def matches(self, plugin_vector: Tuple[str]):
        if len(self.vals) > len(plugin_vector):
            return False  # if input is longer than what plugin knows, this definitely won't fit e.g. aws.us-east-1.something - what is this?
        for ours, theirs in itertools.zip_longest(self.vals, plugin_vector, fillvalue = None):
            if ours == None:
                continue  # not defined in input, so accept all values
            if not ours.matches(theirs):
                return False
        return True


class DisplayMethod(Enum):
    ALL=1
    DEFAULT=2
    MINIMAL=3


def get_inputs():
    _modules = dict(_load_modules())
    for seq, part in enumerate(_iter_parts(sys.argv[1:])):
        args = _parser.parse_args(part)
        _validate_input(args)
        yield from _inflate_input(seq, args, _modules)

def _validate_input(args):
    if args.minimal and args.all:
        raise Exception("Cannot define both minimal and all attributes to display!")


def _inflate_input(seq, args, _modules):
    *m, t = args.something.split(".")
    module_patterns = [StringOrPattern.from_string(m)] if m else [StringOrPattern.from_string(_m) for _m in _modules]
    thing_pattern = StringOrPattern.from_string(t)
    dimensions = Vector.from_tuple(args.dimensions.split(".")) if args.dimensions else None
    display_method = DisplayMethod.ALL if args.all else DisplayMethod.MINIMAL if args.minimal else DisplayMethod.DEFAULT
    # display_filter = re.compile(args.filter) if args.filter else None
    for module_name, module in _modules.items():
        if any(p.matches(module_name) for p in module_patterns):
            concrete_types = [t for t in module.thing_types() if thing_pattern.matches(t)]
            concrete_dimensions = [dims for dims in module.dimensions() if dimensions.matches(dims)] if dimensions else [()]
            for ct, cd in itertools.product(concrete_types, concrete_dimensions):
                yield Input(seq, module_name, module, ct, cd, display_method)


def _iter_parts(args):
    current_part = []
    for a in args:
        if a == "--":
            yield current_part
            current_part = []
        else:
            current_part.append(a)
    yield current_part


def _load_modules():
    if os.getenv("CESSPOOL_MODULE_PATHS"):
        module_paths = os.environ["CESSPOOL_MODULE_PATHS"].split(",")
        sys.path += module_paths
    cesspool_modules = {m for m in find_cesspool_modules()}
    for m in cesspool_modules:
        mod = importlib.import_module(m)
        yield m.split("cesspool_", 1)[-1], mod


def find_cesspool_modules():
    for dir in sys.path:
        yield from {
            os.path.splitext(os.path.basename(full_path))[0]
            for full_path in glob.glob(os.path.join(dir, 'cesspool_*.py'))
        }
