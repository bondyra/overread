import itertools
import json
import re

import aioboto3


with open("./aws.json", "r") as f:
    _config = json.loads(f.read())
with open("/home/tmphome2/.aws/credentials", "r") as f:
    _profiles = re.findall("\[(.*)\]", f.read())
_regions = _config["_regions"]
_sessions = {}


def _session(dimensions):
    key, profile, region = None, None, None
    if len(dimensions) == 1:
        key = profile = dimensions[0]
    if len(dimensions) == 2:
        key = profile, region = dimensions
        key = tuple(key)
    if key not in _sessions:
        kwargs = {}
        if profile:
            kwargs["profile_name"] = profile
        if region:
            kwargs["region_name"] = region
        _sessions[key] = aioboto3.Session(**kwargs)
    return _sessions[key]


async def get(thing_type, dimensions):
    async with _session(dimensions).client("cloudcontrol") as c:
        cloudcontrol_type_name = _config["things"][thing_type]["cc_type_name"]
        ids = await _list_ids(c, cloudcontrol_type_name)
        return [item async for item in _get_resources(c, ids, cloudcontrol_type_name)]


async def _list_ids(client, cloudcontrol_type_name):
    response = await client.list_resources(TypeName=cloudcontrol_type_name)
    return [rd["Identifier"] for rd in response.get('ResourceDescriptions', [])]


async def _get_resources(client, ids, cloudcontrol_type_name):
    for i in ids:
        item = await client.get_resource(TypeName=cloudcontrol_type_name, Identifier = i)
        yield i, item["ResourceDescription"]["Properties"]


def thing_types():
    return list(_config["things"].keys())


def dimensions():
    return itertools.product(_profiles, _regions)


def get_dimension_names():
    return "profile", "region"


def get_default_attrs(thing_type):
    return _config["things"][thing_type].get("default_attrs", None)
