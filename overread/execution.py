import asyncio
from datetime import datetime, date
import json
from typing import Dict, List, Tuple

from overread.graph import Graph
from overread.model import Link, Node, NodeLabel, Result


async def execute(graph: Graph[Node, Link]):
    label_to_results = await _execute_labels(set(node.label for node in graph.iter_all_nodes()))
    for n in graph.iter_all_nodes():
        n.results = label_to_results[n.label]


async def _execute_labels(labels: NodeLabel) -> Dict[NodeLabel, List[Result]]:
    return dict(await asyncio.gather(*(_execute_label(l) for l in labels)))


async def _execute_label(label: NodeLabel) -> Tuple[NodeLabel, List[Result]]:
    return label, [
        Result(id, content, json.dumps(content, default=_serializer))
        async for id, content in label.module.get(label.thing_type, label.place)
    ]


def _serializer(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")
