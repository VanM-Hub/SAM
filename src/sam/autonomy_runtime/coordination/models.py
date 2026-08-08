# Runtime Topology Model - WP-31
# IP-3.2-004 (AO-3.2-001 / ED-3.2-004)
#
# Model topologi runtime - bagaimana beberapa runtime diposisikan & saling
# terhubung dalam satu sistem, sambil tetap tunduk pada Governance.
# Prinsip IP-3.2-004: "Coordinate by model, never by orchestration."
# Runtime boleh memahami keberadaan & hubungan runtime lain, TIDAK boleh
# mengirim perintah/dispatch/eksekusi ke runtime lain. Seluruh output = proposal.
# Per ADR-023: frozen dataclasses (immutable DTO).

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple


@dataclass(frozen=True)
class RuntimeNode:
    """Node runtime dalam topologi - identitas & peran suatu runtime.

    Mencakup identitas runtime, peran (role), lokasi (zone/deployment),
    readiness, dan metadata. Immutable - snapshot dari observasi/registry.
    """

    runtime_id: str
    name: str = ""
    role: str = "worker"  # coordinator | worker | observer | gateway
    zone: str = "default"
    readiness: str = "unknown"  # healthy | degraded | unavailable | unknown
    version: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "runtime_id": self.runtime_id,
            "name": self.name,
            "role": self.role,
            "zone": self.zone,
            "readiness": self.readiness,
            "version": self.version,
            "metadata": dict(self.metadata),
        }

    def is_available(self) -> bool:
        return self.readiness in ("healthy", "degraded")


@dataclass(frozen=True)
class RuntimeTopology:
    """Topologi runtime - kumpulan node + edge koordinasi antar runtime.

    Gambaran statis tentang runtime yang ada dan bagaimana mereka berhubungan.
    Tidak ada instruksi eksekusi; hanya representasi struktur koordinasi.
    """

    topology_id: str
    created_at: str
    nodes: Tuple[RuntimeNode, ...] = ()
    # edge (src, dst): src = prerequisite/authorship; dst = reliant
    edges: Tuple[Tuple[str, str], ...] = ()
    basis: str = "runtime registry observation"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "topology_id": self.topology_id,
            "created_at": self.created_at,
            "nodes": [n.as_dict() for n in self.nodes],
            "edges": [list(e) for e in self.edges],
            "basis": self.basis,
            "metadata": dict(self.metadata),
        }

    def node_count(self) -> int:
        return len(self.nodes)

    def edge_count(self) -> int:
        return len(self.edges)

    def get_node(self, runtime_id: str) -> Optional[RuntimeNode]:
        for node in self.nodes:
            if node.runtime_id == runtime_id:
                return node
        return None

    def runtime_ids(self) -> Tuple[str, ...]:
        return tuple(n.runtime_id for n in self.nodes)


@dataclass(frozen=True)
class CoordinationMetadata:
    """Metadata koordinasi runtime - asal usul, basis bukti, determinisme."""

    coordination_id: str
    created_at: str
    basis: str
    engine: str = "runtime_coordination"
    deterministic: bool = True
    evidence_refs: Tuple[str, ...] = ()
    generated_by: str = "coordination_analysis"
    phase: str = "coordinative"  # coordinative (model only) - bukan operational
    metadata: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "coordination_id": self.coordination_id,
            "created_at": self.created_at,
            "basis": self.basis,
            "engine": self.engine,
            "deterministic": self.deterministic,
            "evidence_refs": list(self.evidence_refs),
            "generated_by": self.generated_by,
            "phase": self.phase,
            "metadata": dict(self.metadata),
        }
