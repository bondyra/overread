import json
import os

from kubernetes_asyncio import client, config
from kubernetes_asyncio.dynamic import DynamicClient


with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "k8s.json"), "r") as f:
    _config = json.loads(f.read())


async def get(thing_type, place):
    ctx, namespace = place
    thing = _config["things"][thing_type]
    if thing.get("global") and namespace != "global":
        raise Exception(f"Cannot query global thing {thing_type} for namespace ({namespace})")
    kwargs = {} if namespace == "global" else {"namespace": namespace}
    async with await config.new_client_from_config(context=ctx) as api:
        client = await DynamicClient(api)
        v1 = await client.resources.get(api_version="v1", kind=thing["kind"])
        response = await v1.get(**kwargs)
        for item in response.items:
            yield item.metadata.name, item.to_dict()


def whats():
    return list(_config["things"].keys())


def color():
    return "blue"


async def wheres():
    contexts, _ = config.list_kube_config_contexts()
    for ctx in contexts:
        async with await config.new_client_from_config(context=ctx["name"]) as api:
            response = await client.CoreV1Api(api).list_namespace()
            for it in response.items:
                yield ctx["name"], it.metadata.name
            yield ctx["name"], "global"


def default_where():
    _, default_context = config.list_kube_config_contexts()
    return default_context["name"], default_context["context"].get("namespace", "default")
