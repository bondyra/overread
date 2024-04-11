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


async def get(thing_type, place):
    thing = _config["things"][thing_type]
    
    async with _session(place).client(thing["client"]) as c:
        response = await getattr(c, thing["method"])()
        for item in response[thing["field"]]:
            yield item[thing["id"]], item


def whats():
    return list(_config["things"].keys())


def color():
    return "orange"


async def wheres():
    for x in itertools.product(_profiles, _regions):
        yield x


def default_where():
    default_session = _session(None)
    return default_session.profile_name, default_session.region_name
