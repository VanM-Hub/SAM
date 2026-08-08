# Dependency Coordination - WP-33
# IP-3.2-004 (AO-3.2-001 / ED-3.2-004)
#
# Memetakan & menganalisis ketergantungan koordinasi antarruntime.
# Koordinasi berdasar dependency: runtime yang menjadi prereq harus "siap"
# sebelum runtime yang bergantung padanya dapat dikoordinasikan.
# Hanya model & proposal - tidak ada dispatch/eksekusi.

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from sam.autonomy_runtime.coordination.engine import CoordinationGraph
from sam.autonomy_runtime.coordination.models import RuntimeTopology


@dataclass(frozen=True)
class CoordinationBlocker:
    """Blocker koordinasi - runtime prereq yang belum siap (proposal, bukan aksi)."""

    runtime_id: str
    missing_prereq: str
    reason: str = "prerequisite runtime not ready for coordination"

    def as_dict(self) -> Dict[str, Any]:
        return {
            "runtime_id": self.runtime_id,
            "missing_prereq": self.missing_prereq,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class DependencyCoordinationPlan:
    """Rencana koordinasi berdasar dependency (proposal, urutan, bukan eksekusi)."""

    plan_id: str
    ordered: Tuple[str, ...] = ()  # urutan koordinasi yang diusulkan
    blockers: Tuple[CoordinationBlocker, ...] = ()
    rationale: str = ""
    is_proposal_only: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "ordered": list(self.ordered),
            "blockers": [b.as_dict() for b in self.blockers],
            "rationale": self.rationale,
            "is_proposal_only": self.is_proposal_only,
            "metadata": dict(self.metadata),
        }

    def ordered_count(self) -> int:
        return len(self.ordered)

    def blocker_count(self) -> int:
        return len(self.blockers)

    def is_blocked(self) -> bool:
        return len(self.blockers) > 0


class DependencyCoordinator:
    """Koordinasi berdasar dependency antarruntime (deterministik, proposal-only)."""

    def build_plan(
        self,
        topology: RuntimeTopology,
        graph: CoordinationGraph,
        plan_id: str = "",
    ) -> DependencyCoordinationPlan:
        ordered, blockers = self._topo_order(topology, graph)
        plan_id = plan_id or self._stable_id(topology.topology_id)
        return DependencyCoordinationPlan(
            plan_id=plan_id,
            ordered=tuple(ordered),
            blockers=tuple(blockers),
            rationale=(
                "Dependency-aware coordination order; blockers identify "
                "prerequisite runtimes not ready; proposal only"
            ),
            is_proposal_only=True,
            metadata={"deterministic": True},
        )

    # --- helpers ---

    def _topo_order(
        self,
        topology: RuntimeTopology,
        graph: CoordinationGraph,
    ) -> Tuple[List[str], List[CoordinationBlocker]]:
        """Topological order (prereq dulu) + blocker untuk runtime unavailable.

        Runtime yang prereq-nya unavailable dianggap ter-blocker dan disisipkan
        di akhir urutan (tidak dieksekusi, hanya diusulkan posisinya).
        """
        available = {
            n.runtime_id for n in topology.nodes if n.is_available()
        }
        prereq: Dict[str, List[str]] = {}
        for e in graph.edges:
            prereq.setdefault(e.dst, []).append(e.src)

        remaining = set(topology.runtime_ids())
        ordered: List[str] = []
        blockers: List[CoordinationBlocker] = []

        while remaining:
            # node yang semua prereq-nya sudah di-order (atau tak punya prereq)
            ready = sorted(
                [
                    rid for rid in remaining
                    if all(p in ordered for p in prereq.get(rid, []))
                ]
            )
            if not ready:
                # cycle / unresolved: sisipkan sisa (tie-break id)
                ready = sorted(remaining)
                break
            for rid in ready:
                remaining.discard(rid)
                ordered.append(rid)
        # runtimes yang belum ter-order karena cycle ditambahkan deterministic
        for rid in sorted(remaining):
            if rid not in ordered:
                ordered.append(rid)

        # blocker: runtime yang prereq-nya unavailable
        for rid in ordered:
            for p in prereq.get(rid, []):
                if p not in available:
                    blockers.append(
                        CoordinationBlocker(runtime_id=rid, missing_prereq=p)
                    )
        blockers.sort(key=lambda b: (b.runtime_id, b.missing_prereq))
        return ordered, blockers

    @staticmethod
    def _stable_id(seed: str) -> str:
        import hashlib

        return "dp-" + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:8]
