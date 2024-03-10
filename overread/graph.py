from collections import defaultdict
from typing import Callable, Dict, Generic, Iterable, List, Tuple, TypeVar


T = TypeVar("T")
S = TypeVar("S")


class Graph(Generic[T, S]):
    def __init__(self, nodes: Iterable[T], id_func: Callable[[T], str], edges: Iterable[Tuple[str, str, S]]):
        self._id_func = id_func
        self._id_to_nodes = defaultdict(list)
        for n in nodes:
            self._id_to_nodes[self._id_func(n)].append(n)
        self._parent_to_children = defaultdict(list)
        self._child_to_parents = defaultdict(list)
        for e in edges:
            if e[0] not in self._id_to_nodes:
                raise Exception(f"Left edge element \"{e[0]}\" does not exist!")
            if e[1] not in self._id_to_nodes:
                raise Exception(f"Right edge element \"{e[1]}\" does not exist!")
            self._parent_to_children[e[0]].append((e[1], e[2]))
            self._child_to_parents[e[1]].append((e[0], e[2]))

    def get_root_ids(self) -> Iterable[str]:
        return [id for id in self._id_to_nodes if not any(self._child_to_parents[id])]

    def get_children_id_and_edge(self, parent_id: str) -> Iterable[Tuple[str, S]]:
        return [(cid, s) for cid, s in self._parent_to_children[parent_id]]

    def iter_nodes(self, id: str) -> Iterable[T]:
        return self._id_to_nodes[id]

    def iter_all_nodes(self) -> Iterable[T]:
        for id in self._id_to_nodes:
            yield from self.iter_nodes(id)
