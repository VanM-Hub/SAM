# Readiness-based Planner - WP-15
# IP-3.2-002 (AO-3.2-001 / ED-3.2-002)
#
# Prioritas berdasarkan readiness & health. Mengurutkan kandidat kerja dengan
# mempertimbangkan kondisi kesiapan komponen dan health-nya. Deterministik,
# berbasis observasi (readiness + health), TANPA aksi. Proposal saja.
#
# Prinsip: plan, never decide.

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from sam.autonomy_runtime.planning.models import PlanStep, PlanningContext

_WEIGHT = {
    "unavailable": 0,   # tidak bisa dikerjakan sekarang -> bobot rendah utk kelayakan
    "unknown": 1,
    "degraded": 2,
    "healthy": 3,
}


@dataclass(frozen=True)
class ReadinessPriority:
    """Hasil prioritisasi berbasis readiness untuk satu step (immutable)."""

    step_id: str
    target: str
    readiness_weight: int
    priority_score: int  # skor gabungan (semakin tinggi = layak dikerjakan lebih dulu)
    basis: Tuple[str, ...]  # label kondisi yang menjadi basis penilaian

    def as_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "target": self.target,
            "readiness_weight": self.readiness_weight,
            "priority_score": self.priority_score,
            "basis": list(self.basis),
        }


@dataclass(frozen=True)
class ReadinessPlanResult:
    """Urutan langkah yang diprioritaskan berdasarkan readiness (immutable)."""

    plan_id: str
    priorities: Tuple[ReadinessPriority, ...] = ()
    ordered_step_ids: Tuple[str, ...] = ()
    ready_targets: Tuple[str, ...] = ()
    not_ready_targets: Tuple[str, ...] = ()

    def as_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "priorities": [p.as_dict() for p in self.priorities],
            "ordered_step_ids": list(self.ordered_step_ids),
            "ready_targets": list(self.ready_targets),
            "not_ready_targets": list(self.not_ready_targets),
        }


class ReadinessBasedPlanner:
    """Memprioritaskan langkah berdasarkan readiness & health komponen."""

    def __init__(self, context: PlanningContext) -> None:
        self._context = context

    def prioritize(self, steps: Tuple[PlanStep, ...], plan_id: str = "") -> ReadinessPlanResult:
        """Urutkan step berdasarkan readiness komponen target (deterministik).

        Skor = readiness_weight target; higher dulu. Tie-break step_id.
        """
        scores: List[ReadinessPriority] = []
        for step in steps:
            weight = self._weight_of(step.target)
            score = _combined_score(weight, step.priority)
            basis = self._basis_of(step.target)
            scores.append(ReadinessPriority(
                step_id=step.step_id,
                target=step.target,
                readiness_weight=weight,
                priority_score=score,
                basis=basis,
            ))
        ordered = sorted(scores, key=lambda p: (-p.priority_score, p.step_id))
        ordered_ids = tuple(p.step_id for p in ordered)
        ready = tuple(p.target for p in ordered if p.readiness_weight >= _WEIGHT["degraded"])
        not_ready = tuple(p.target for p in ordered if p.readiness_weight < _WEIGHT["degraded"])
        return ReadinessPlanResult(
            plan_id=plan_id,
            priorities=tuple(ordered),
            ordered_step_ids=ordered_ids,
            ready_targets=ready,
            not_ready_targets=not_ready,
        )

    # --- internal ---

    def _weight_of(self, target: str) -> int:
        """Bobot readiness target dari context (read-only)."""
        if target in self._context.unavailable_components:
            return _WEIGHT["unavailable"]
        if target in self._context.degraded_components:
            return _WEIGHT["degraded"]
        if target in self._context.healthy_components:
            return _WEIGHT["healthy"]
        return _WEIGHT["unknown"]

    def _basis_of(self, target: str) -> Tuple[str, ...]:
        basis: List[str] = []
        if target in self._context.unavailable_components:
            basis.append("unavailable")
        if target in self._context.degraded_components:
            basis.append("degraded")
        if target in self._context.healthy_components:
            basis.append("healthy")
        return tuple(basis) if basis else ("unknown",)


def _combined_score(readiness_weight: int, step_priority: int) -> int:
    """Skor gabungan: readiness dominan, step_priority sebagai pengikat.

    Skor = readiness_weight * 10 + step_priority. Deterministik.
    """
    return readiness_weight * 10 + step_priority
