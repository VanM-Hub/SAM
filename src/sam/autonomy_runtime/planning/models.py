# Runtime Planning Model - WP-11
# IP-3.2-002 (AO-3.2-001 / ED-3.2-002)
#
# Immutable planning DTO, planning state, planning metadata.
# Prinsip IP-3.2-002: "Plan, never decide." Runtime menyusun rencana,
# tidak pernah mengambil keputusan konstitusional. Seluruh artefak = proposal
# deterministik, bukan aksi. Per ADR-023: frozen dataclasses (immutable DTO).

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class PlanningContext:
    """Konteks perencanaan - snapshot kondisi runtime yang diamati.

    Menyimpan kondisi runtime (state) yang menjadi dasar penyusunan rencana.
    Bersifat immutable; dibuat dari hasil observasi + diagnostik.
    """

    source: str
    runtime_state_id: Optional[str] = None
    overall_health: str = "unknown"
    readiness_level: str = "unknown"
    healthy_components: Tuple[str, ...] = ()
    degraded_components: Tuple[str, ...] = ()
    unavailable_components: Tuple[str, ...] = ()
    dependency_edges: Tuple[Tuple[str, str], ...] = ()
    metadata: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "runtime_state_id": self.runtime_state_id,
            "overall_health": self.overall_health,
            "readiness_level": self.readiness_level,
            "healthy_components": list(self.healthy_components),
            "degraded_components": list(self.degraded_components),
            "unavailable_components": list(self.unavailable_components),
            "dependency_edges": [list(e) for e in self.dependency_edges],
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class PlanStep:
    """Satu langkah kerja dalam rencana operasional (proposal, bukan aksi).

    Setiap langkah adalah ide kerja yang DIUSULKAN - tidak menjalankan apa pun.
    """

    step_id: str
    action: str  # nama kerja yang diusulkan (label, bukan eksekusi)
    target: str  # komponen/pemilik kerja yang dituju
    prerequisite_ids: Tuple[str, ...] = ()
    depends_on: Tuple[str, ...] = ()
    readiness_gate: str = "none"  # readiness yang harus dipenuhi sebelum langkah ini layak
    priority: int = 0
    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "action": self.action,
            "target": self.target,
            "prerequisite_ids": list(self.prerequisite_ids),
            "depends_on": list(self.depends_on),
            "readiness_gate": self.readiness_gate,
            "priority": self.priority,
            "reason": self.reason,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class PlanningMetadata:
    """Metadata rencana - asal usul, basis bukti, determinisme."""

    plan_id: str
    created_at: str
    basis: str  # deskripsi basis yang diamati (observation + diagnostics)
    engine: str = "runtime_planning"
    deterministic: bool = True
    evidence_refs: Tuple[str, ...] = ()
    generated_by: str = "observation_diagnostics"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "created_at": self.created_at,
            "basis": self.basis,
            "engine": self.engine,
            "deterministic": self.deterministic,
            "evidence_refs": list(self.evidence_refs),
            "generated_by": self.generated_by,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class RuntimePlan:
    """Rencana operasional runtime - immutable, proposal-only.

    Berisi urutan kerja yang diusulkan beserta alasannya. Tidak pernah
    mengeksekusi, mengubah Mission/Workflow/Policy/Governance, atau
    mengambil keputusan konstitusional. Hanya proposal deterministik.
    """

    plan_id: str
    context: PlanningContext
    metadata: PlanningMetadata
    steps: Tuple[PlanStep, ...] = ()
    created_at: str = ""
    state: str = "proposed"  # proposed | ready | blocked
    summary: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "created_at": self.created_at,
            "state": self.state,
            "summary": self.summary,
            "context": self.context.as_dict(),
            "metadata": self.metadata.as_dict(),
            "steps": [s.as_dict() for s in self.steps],
        }

    # --- query read-only ---

    def step_count(self) -> int:
        return len(self.steps)

    def step_ids(self) -> List[str]:
        return [s.step_id for s in self.steps]

    def required_targets(self) -> List[str]:
        return list(dict.fromkeys(s.target for s in self.steps))

    def is_proposal_only(self) -> bool:
        """Rencana ini murni proposal - tidak ada langkah yang memicu aksi."""
        return all(s.action.startswith("plan_") or s.priority >= 0 for s in self.steps)
