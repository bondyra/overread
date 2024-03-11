import asyncio
from typing import Dict, List, Tuple

from overread.graph import Graph
from overread.model import Link, Node, NodeLabel, Result


def execute(graph: Graph[Node, Link]):
    label_to_results = asyncio.run(_execute_labels(set(node.label for node in graph.iter_all_nodes())))
    for n in graph.iter_all_nodes():
        n.results = label_to_results[n.label]


async def _execute_labels(labels: NodeLabel) -> Dict[NodeLabel, List[Result]]:
    return dict(await asyncio.gather(*(_execute_label(l) for l in labels)))


async def _execute_label(label: NodeLabel) -> Tuple[NodeLabel, List[Result]]:
    return label, [Result(id, blob) for id, blob in await label.module.get(label.thing_type, label.place)]
