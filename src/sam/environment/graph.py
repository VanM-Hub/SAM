"""Environment-adaptive: model graph relasi antar-entitas.

Membangun model hubungan dari hasil discovery (tanpa asumsi aplikasi):
  - process  --LISTENS--> port
  - process  <--OWNS-->   port (sama pid)
  - file     --SCANNED--> (ada di direktori yang sama)

Graph ini menjadi dasar penentuan kandidat ward dan investigasi root cause.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from sam.environment.entity import Entity, EntityKind


class EdgeKind:
    LISTENS = "listens"
    OWNS = "owns"
    CO_LOCATED = "co_located"
    REFERENCES = "references"
    PROVIDES = "provides"


@dataclass
class Edge:
    source: str
    target: str
    kind: str
    evidence: str = ""   # alasan (fakta), bukan asumsi

    def as_dict(self) -> Dict[str, str]:
        return {
            "source": self.source,
            "target": self.target,
            "kind": self.kind,
            "evidence": self.evidence,
        }


class EntityGraph:
    """Graph sederhana: nodes = entity id, edges = relasi.

    API:
      add_entity(e) / add_edge(a, b, kind, evidence)
      neighbors(id) / find(kind, attr_key, attr_value)
      candidate_by_kind(kind) -> daftar node dengan edge kind tertentu
    """

    def __init__(self) -> None:
        self._nodes: Dict[str, Entity] = {}
        self._edges: List[Edge] = []

    # --- mutation ---

    def add_entity(self, e: Entity) -> None:
        self._nodes[e.id] = e

    def add_edge(self, source: str, target: str, kind: str,
                 evidence: str = "") -> None:
        # jangan duplikasi edge identik
        if any(x.source == source and x.target == target and x.kind == kind
               for x in self._edges):
            return
        self._edges.append(Edge(source, target, kind, evidence))

    # --- query ---

    def node(self, eid: str) -> Optional[Entity]:
        return self._nodes.get(eid)

    def nodes(self) -> List[Entity]:
        return list(self._nodes.values())

    def edges(self) -> List[Edge]:
        return list(self._edges)

    def neighbors(self, eid: str, kind: Optional[str] = None) -> List[str]:
        out: List[str] = []
        for x in self._edges:
            if kind and x.kind != kind:
                continue
            if x.source == eid:
                out.append(x.target)
            elif x.target == eid:
                out.append(x.source)
        return out

    def find(self, kind: EntityKind, attr_key: str,
             attr_value: object) -> List[Entity]:
        return [
            e for e in self._nodes.values()
            if e.kind == kind and e.attributes.get(attr_key) == attr_value
        ]

    def nodes_of_kind(self, kind: EntityKind) -> List[Entity]:
        return [e for e in self._nodes.values() if e.kind == kind]

    def edges_to(self, eid: str) -> List[Edge]:
        return [x for x in self._edges if x.target == eid]

    # --- builder dari scan ---

    @staticmethod
    def from_scan(entities: List[Entity]) -> "EntityGraph":
        g = EntityGraph()
        for e in entities:
            g.add_entity(e)
        _build_relations(g, entities)
        return g


def _build_relations(g: EntityGraph, entities: List[Entity]) -> None:
    # port --owns--> process berdasarkan pid
    for port in entities:
        if port.kind != EntityKind.PORT:
            continue
        pid = port.attributes.get("pid")
        if not pid:
            continue
        for proc in entities:
            if (proc.kind == EntityKind.PROCESS
                    and proc.attributes.get("pid") == pid):
                g.add_edge(port.id, proc.id, EdgeKind.OWNS,
                           evidence=f"port pid={pid} == process pid={pid}")

    # co-located file (direktori sama) -> group
    dirs: Dict[str, List[str]] = {}
    for f in entities:
        if f.kind != EntityKind.FILE:
            continue
        p = f.attributes.get("path", "")
        d = p.rsplit("\\", 1)[0] if "\\" in p else p.rsplit("/", 1)[0]
        dirs.setdefault(d, []).append(f.id)
    for d, ids in dirs.items():
        if len(ids) < 2:
            continue
        base = ids[0]
        for other in ids[1:]:
            g.add_edge(base, other, EdgeKind.CO_LOCATED,
                       evidence=f"same directory {d}")
