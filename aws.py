import itertools
import json
import re

import aioboto3


content = None
creds = None
_sessions = {}
_profiles = []
_regions = []


def init():
    global content, creds
    with open("./aws.json", "r") as f:
        content = json.loads(f.read())
    with open("/home/tmphome2/.aws/credentials", "r") as f:
        creds = f.read()
    _profiles = re.findall("\[(.*)\]", creds)
    _regions = content["_regions"]


def _session(group):
    if group not in _sessions:
        profile, region = group[:2]
        _sessions[group] = aioboto3.Session(profile_name=profile, region_name=region)
    return _sessions[group]


async def get(group, resource_type):
    async with _session(group).client("cloudcontrol") as c:
        ids = await _list_ids(c, content[resource_type]["cc_type_name"])
        return [item async for item in _get_resources(c, ids, content[resource_type]["cc_type_name"])]


async def _list_ids(client, type_name):
    response = await client.list_resources(TypeName=type_name)
    return [rd["Identifier"] for rd in response.get('ResourceDescriptions', [])]


async def _get_resources(client, ids, type_name):
    for i in ids:
        item = await client.get_resource(TypeName=type_name, Identifier = i)
        yield {"_id": i, **json.loads(item["ResourceDescription"]["Properties"])}


def resource_types():
    return list(content.keys())


def groups():
    return itertools.product(_profiles, _regions)


def mentions(resource_type):
    return content.get(resource_type, {}).get("mentions")
