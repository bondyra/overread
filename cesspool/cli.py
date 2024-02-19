import itertools
import json
from typing import Dict, List

import yaml

from cesspool.input import DisplayMethod, get_inputs, Input
from cesspool.execution import execute, Result


def main():
    inputs = list(get_inputs())
    results = list(execute(inputs))
    joined_results = list(process_join(inputs, results))
    rendered_results = render_results({i.seq: i for i in inputs}, joined_results, None, -1)
    display(rendered_results)


def process_join(inputs: Dict[int, Input], results: List[Result]):
    parent_ids = {None}
    for input in inputs:
        new_parent_ids = set()
        for parent_id in parent_ids:
            for it in iter_metadata(input, results):
                if not parent_id:  # root
                    yield it
                    new_parent_ids.add(it["id"])  # set a context for next layer
                else:
                    mention = get_first_mention_of_parent(it["data"], parent_id)
                    if mention:
                        new_parent_ids.add(it["id"])  # set a context for next layer
                        yield {
                            **it,
                            "mention": mention,
                            "pid": parent_id
                        }
        parent_ids = new_parent_ids


def iter_metadata(input: Input, results: List[Result]):
    for r in results:
        if r.seq != input.seq:
            continue
        for id, blob in r.things:
            maybe_obj = try_json(blob)
            dim_names = input.module.get_dimension_names()
            yield {
                "id": id,
                "seq": r.seq,
                "type": r.type,
                "data": maybe_obj or blob,
                **{f"dim_{dim_name or 'dim_' + index}": dim for dim_name, dim, index in itertools.zip_longest(dim_names, r.dimensions, range(len(r.dimensions)))},
            }


def try_json(blob):
    try:
        return json.loads(blob)
    except json.JSONDecodeError:
        return None


def get_first_mention_of_parent(item, parent_id):
    if isinstance(item, dict):
        return _get_first_jsonpath_match(item, parent_id)
    else:
        return _get_first_plaintext_match(item, parent_id)


def _get_first_jsonpath_match(item, id):
    if id not in str(item):
        return None
    stack = [(item, "$")]
    while stack:
        current_obj, current_path = stack.pop()
        if isinstance(current_obj, dict):
            for key, value in current_obj.items():
                path = f"{current_path}.{key}"
                stack.append((value, path))
        elif isinstance(current_obj, list):
            for index, value in enumerate(current_obj):
                path = f"{current_path}[{index}]"
                stack.append((value, path))
        elif isinstance(current_obj, str) and current_obj == id:
            return current_path
    return None


def _get_first_plaintext_match(blob, id):
    try:
        index = blob.index(id)
    except ValueError:
        return None
    else:
        # it's a pretty print
        start, end = max(0, index - 10), min(len(blob), index + len(id) + 10)
        prefix = f"{'...' if start > 0 else ''}{blob[start:index]}"
        suffix = f"{blob[(index + len(id)):end]}{'...' if end < len(blob) else ''}"
        return f"{prefix}{id}{suffix}"


def render_results(inputs_dict, results, pid, pseq):
    return {
        f"{inputs_dict[pseq + 1].module_name}.{typ}": {  # TODO: just a list of render_id if minimal?
            render_id(inputs_dict[pseq + 1], r): {
                **render_obj(inputs_dict[pseq + 1], r),
                **render_results(inputs_dict, results, r["id"], r["seq"])
            }
            for r in results if r["type"] == typ and r["seq"] == pseq + 1 and r.get("pid") == pid
        }
        for typ in set(r["type"] for r in results if r.get("pid") == pid and r["seq"] == pseq + 1)
    }


def render_id(_, r):
    return r["id"]


def render_obj(input: Input, r):
    header = {
        "_in": ".".join((v or "(default)") for k, v in r.items() if k.startswith("dim_"))
    }
    if "mention" in r:
        header["_via"] = r["mention"]
    data = r["data"]
    if isinstance(r["data"], dict):
        if input.display_method == DisplayMethod.DEFAULT:
            defaults = input.module.get_default_attrs(r["type"]) or r["data"].keys()
            data = {k: r["data"][k] for k in defaults}
        elif input.display_method == DisplayMethod.MINIMAL:
            data = {}

    return {**header, **data}


def display(results):
    print(yaml.dump(results, sort_keys=False))
