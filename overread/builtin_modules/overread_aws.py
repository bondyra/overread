import itertools
import json
import os
import re

import aioboto3


with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "aws.json"), "r") as f:
    _config = json.loads(f.read())
with open(f"{os.environ['HOME']}/.aws/credentials", "r") as f:
    _profiles = re.findall("\[(.*)\]", f.read())
_regions = _config["_regions"]
_sessions = {}


def _session(place):
    key, profile, region = None, None, None
    if not place:
        pass
    elif len(place) == 1:
        key = profile = place[0]
    elif len(place) == 2:
        key = profile, region = place
        key = tuple(key)
    if key not in _sessions:
        kwargs = {}
        if profile:
            kwargs["profile_name"] = profile
        if region:
            kwargs["region_name"] = region
        _sessions[key] = aioboto3.Session(**kwargs)
    return _sessions[key]


# interface member
async def get(thing_type, place):
    async with _session(place).client("cloudcontrol") as c:
        thing = _config["things"][thing_type]
        resource_model = thing.get("resource_model")
        if resource_model:
            results = await _get(c, thing["cc_type_name"])
            for i in range(len(results)):
                new_item = results[i][1]
                for attr, v in resource_model.items():
                    new_item[attr] = [
                        r
                        for _, r in await _get(
                            c, v["cc_type_name"], ResourceModel=f'{{"{v["parent_field"]}":"{results[i][0]}"}}'
                        )
                    ]
                yield results[i][0], new_item
        else:
            for id, it in await _get(c, thing["cc_type_name"]):
                yield id, it


async def _get(c, cloudcontrol_type_name, **list_resources_kwargs):
    ids = await _list_ids(c, cloudcontrol_type_name, **list_resources_kwargs)
    return [item async for item in _get_resources(c, ids, cloudcontrol_type_name)]


async def _list_ids(client, cloudcontrol_type_name, **kwargs):
    response = await client.list_resources(TypeName=cloudcontrol_type_name, **kwargs)
    return [rd["Identifier"] for rd in response.get("ResourceDescriptions", [])]


async def _get_resources(client, ids, cloudcontrol_type_name):
    for i in ids:
        item = await client.get_resource(TypeName=cloudcontrol_type_name, Identifier=i)
        yield i, json.loads(item["ResourceDescription"]["Properties"])


# interface member
def thing_types():
    return list(_config["things"].keys())


# interface member
def prettify(thing_type, thing):
    result = {da: thing[da] for da in _config["things"][thing_type].get("default_attrs", []) if da in thing}
    resource_model = _config["things"][thing_type].get("resource_model")
    if resource_model:
        for rm_attr, v in resource_model.items():
            result[rm_attr] = [
                {da: thing_it[da] for da in v["default_attrs"] if da in thing_it} for thing_it in thing.get(rm_attr, [])
            ]
    return result


# interface member
def color():
    return "\033[33m"  # foreground yellow


# interface member
async def places():
    for x in itertools.product(_profiles, _regions):
        yield x


# interface member
def default_place():
    default_session = _session(None)
    return default_session.profile_name, default_session.region_name
