import json

from kubernetes_asyncio import client, config
from kubernetes_asyncio.dynamic import DynamicClient


with open("k8s.json", "r") as f:
    _config = json.loads(f.read())


# interface member
async def get(thing_type, place):
    ctx, namespace = place
    thing = _config["things"][thing_type]
    if thing.get("global") and namespace != "global":
        raise Exception(f"Cannot query global thing {thing_type} for namespace ({namespace})")
    kwargs = {} if namespace == "global" else {"namespace": namespace}
    async with await config.new_client_from_config(context=ctx) as api:
        client = await DynamicClient(api)
        v1 = await client.resources.get(api_version="v1", kind=thing_type.capitalize())
        response = await v1.get(**kwargs)
        for item in response.items:
            yield item.metadata.name, item.to_dict()


# interface member
def thing_types():
    return list(_config["things"].keys())


DEFAULT_METADATA = {"creation_timestamp", "labels", "annotations"}
DEFAULT_SPEC = {}
DEFAULT_STATUS = {"phase"}


# interface member
def prettify(thing_type, thing):
    config = _config["things"][thing_type]
    return {
        "metadata": {
            k: v
            for k, v in thing.get("metadata", {}).items()
            if (k in DEFAULT_METADATA or k in config.get("default_metadata", {})) and v
        },
        "spec": {
            k: v
            for k, v in thing.get("spec", {}).items()
            if (k in DEFAULT_SPEC or k in config.get("default_spec", {})) and v
        },
        "status": {
            k: v
            for k, v in thing.get("status", {}).items()
            if (k in DEFAULT_STATUS or k in config.get("default_status", {})) and v
        },
    }


# interface member
def color():
    return "\033[34m"  # blue


# interface member
async def places():
    contexts, _ = config.list_kube_config_contexts()
    for ctx in contexts:
        async with await config.new_client_from_config(context=ctx["name"]) as api:
            response = await client.CoreV1Api(api).list_namespace()
            for it in response.items:
                yield ctx["name"], it.metadata.name
            yield ctx["name"], "global"


# interface member
def default_place():
    _, default_context = config.list_kube_config_contexts()
    return default_context["name"], default_context["context"].get("namespace", "default")
