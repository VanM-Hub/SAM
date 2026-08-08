# Planning Optimization - WP-16
# IP-3.2-002 (AO-3.2-001 / ED-3.2-002)
#
# Optimasi urutan (deterministic heuristic, BUKAN AI/LLM).
# Memperbaiki urutan kerja dengan heuristik deterministik: meminimalkan
# blocking (prasyarat dulu), mengoptimalkan kesiapan (ready-first),
# menghindari langkah yang tidak bisa dikerjakan menunda langkah yang bisa.
# Murni read-only - menghasilkan urutan proposal yang lebih baik, tanpa aksi.
#
# Prinsip: plan, never decide.

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from sam.autonomy_runtime.planning.models import PlanStep, PlanningContext


@dataclass(frozen=True)
class OptimizationResult:
    """Hasil optimasi urutan (immutable). Menjelaskan perubahan vs semula."""

    plan_id: str
    original_order: Tuple[str, ...]
    optimized_order: Tuple[str, ...]
    changed: bool
    improvements: Tuple[str, ...]  # deskripsi perbaikan yang diterapkan
    heuristic: str = "deterministic_priority_readiness"

    def as_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "original_order": list(self.original_order),
            "optimized_order": list(self.optimized_order),
            "changed": self.changed,
            "improvements": list(self.improvements),
            "heuristic": self.heuristic,
        }


class PlanningOptimizer:
    """Mengoptimalkan urutan step dengan heuristik deterministik."""

    def __init__(self, context: PlanningContext) -> None:
        self._context = context

    def optimize(self, steps: Tuple[PlanStep, ...], plan_id: str = "") -> OptimizationResult:
        """Optimalkan urutan step; kembalikan hasil + penjelasan perubahan."""
        original_order = tuple(s.step_id for s in steps)
        improvements: List[str] = []

        # 1) dependency-first: prasyarat sebelum dependents (selidiki blocker)
        ordered = list(steps)
        moved = self._dependency_forward(ordered, improvements)
        if moved:
            improvements.append("dependency-order: prerequisites placed before dependents")

        # 2) readiness-first: langkah yang siap dikerjakan (target tersedia/tidak
        #    terblokir) didahulukan, tanpa mengorbankan dependency order
        ordered = self._readiness_forward(ordered, improvements)

        optimized_order = tuple(s.step_id for s in ordered)
        changed = original_order != optimized_order
        return OptimizationResult(
            plan_id=plan_id,
            original_order=original_order,
            optimized_order=optimized_order,
            changed=changed,
            improvements=tuple(improvements),
        )

    # --- heuristics ---

    def _dependency_forward(self, steps: List[PlanStep], improvements: List[str]) -> bool:
        """Pindahkan langkah prasyarat lebih dulu daripada dependent-nya.

        Menggunakan bobot kedalaman dependensi (semakin dalam = semakin dulu).
        Stabil: urutan relatif step berbobot sama dipertahankan agar deterministik.
        """
        target_to_step = {s.target: s for s in steps}

        def depth(target: str) -> int:
            """Kedalaman prasyarat tertinggi di bawah target (transitif)."""
            best = 0
            for dep in self._dependencies_of(target):
                if dep in target_to_step:
                    best = max(best, 1 + depth(dep))
            return best

        weight = {s.step_id: depth(s.target) for s in steps}
        stable = {s.step_id: i for i, s in enumerate(steps)}
        ordered = sorted(
            steps, key=lambda s: (-weight[s.step_id], stable[s.step_id])
        )
        if [s.step_id for s in ordered] != [s.step_id for s in steps]:
            improvements.append(
                "dependency-order: prerequisites placed before dependents"
            )
            steps[:] = ordered
            return True
        return False

    def _dependencies_of(self, target: str) -> List[str]:
        return [src for src, dst in self._context.dependency_edges if dst == target]

    def _readiness_forward(self, steps: List[PlanStep], improvements: List[str]) -> List[PlanStep]:
        """Stabil: langkah yang targetnya ready (healthy/degraded) didahulukan.

        Menjaga urutan relatif step yang setara (stability) agar deterministik.
        """
        order = {
            s.step_id: i for i, s in enumerate(steps)
        }
        rank = {
            s.step_id: 0 if s.target in (
                self._context.healthy_components + self._context.degraded_components
            ) else 1
            for s in steps
        }
        sorted_steps = sorted(
            steps, key=lambda s: (rank[s.step_id], order[s.step_id])
        )
        if [s.step_id for s in sorted_steps] != [s.step_id for s in steps]:
            improvements.append(
                "readiness-order: ready targets placed before unavailable ones"
            )
        return sorted_steps
