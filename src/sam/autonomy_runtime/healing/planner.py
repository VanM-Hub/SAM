# Self-Healing Planner - WP-24
# IP-3.2-003 (AO-3.2-001 / ED-3.2-003)
#
# Mengubah RecoveryStrategy menjadi candidate SelfHealingPlan (proposal only).
# healing/ TIDAK berisi executor/mutation - hanya planner & model.
# Menerapkan dependency-aware & readiness-aware sequencing.

from typing import Dict, List, Tuple

from sam.autonomy_runtime.recovery.strategy import RecoveryStrategy
from sam.autonomy_runtime.recovery.models import RecoveryContext
from sam.autonomy_runtime.healing.models import HealingStep, SelfHealingPlan

# Prioritas langkah self-healing: lebih tinggi = lebih dulu diusulkan
_PRIORITY = {
    "recover_restore": 30,
    "recover_replicate": 25,
    "recover_replace": 22,
    "recover_retry": 18,
    "recover_rebalance": 15,
    "recover_wait": 5,
}


class SelfHealingPlanner:
    """Menyusun candidate SelfHealingPlan dari RecoveryStrategy.

    Deterministik: setiap action strategi menjadi HealingStep dengan urutan
    dependency-aware (prerequisite siap dulu) & readiness-aware. Tidak
    mengubah input, tidak mengeksekusi apa pun.
    """

    def build_plan(
        self,
        strategy: RecoveryStrategy,
        context: RecoveryContext,
        plan_id: str = "",
    ) -> SelfHealingPlan:
        steps: List[HealingStep] = []
        parents = _dependency_map(context)

        for action in strategy.actions:
            step_id = "heal-{}".format(action.sequence)
            prereqs = _prereqs_of(action.target, parents)
            priority = _PRIORITY.get(action.action, 10)
            steps.append(
                HealingStep(
                    step_id=step_id,
                    action=action.action,
                    target=action.target,
                    strategy=action.strategy,
                    prerequisite_ids=prereqs,
                    priority=priority,
                    reason=action.rationale,
                )
            )

        # dependency-aware ordering: prerequisite siap sebelum dependen
        ordered = _dependency_order(steps, parents)
        steps_tuple = tuple(ordered)

        plan_id = plan_id or self._stable_id(strategy.strategy_id)
        return SelfHealingPlan(
            plan_id=plan_id,
            context_state_id=context.state_id,
            strategy_id=strategy.strategy_id,
            steps=steps_tuple,
            state="proposed",
            readiness_gate=strategy.readiness_gate,
            rationale=(
                "Candidate self-healing plan derived from recovery strategy {}; "
                "proposal only, no execution".format(strategy.strategy_id)
            ),
            metadata={"deterministic": True, "source": "recovery_strategy"},
        )

    @staticmethod
    def _stable_id(seed: str) -> str:
        import hashlib

        return "shp-" + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:8]


def _dependency_map(context: RecoveryContext) -> Dict[str, Tuple[str, ...]]:
    """Peta komponen -> tuple prereq (komponen yang harus siap dulu)."""
    parents: Dict[str, list] = {}
    for src, dst in context.dependency_edges:
        # (src, dst): dst butuh src siap dulu
        parents.setdefault(dst, []).append(src)
    return {k: tuple(v) for k, v in parents.items()}


def _prereqs_of(target: str, parents: Dict[str, Tuple[str, ...]]) -> Tuple[str, ...]:
    return tuple(parents.get(target, ()))


def _dependency_order(
    steps: List[HealingStep], parents: Dict[str, Tuple[str, ...]]
) -> List[HealingStep]:
    """Urutkan langkah dependency-first: prereq sebelum dependen.

    Dependency-first topological ordering dengan tie-break deterministik
    (priority turun, lalu step_id naik). Jika ada cycle, jatuh ke urutan
    priority (tidak gagal). Sederhana dan deterministik - strategi recovery
    umumnya DAG kecil.
    """
    by_id = {s.step_id: s for s in steps}
    by_target = {s.target: s for s in steps}

    def target_ready(step: HealingStep, emitted: set) -> bool:
        for prereq in parents.get(step.target, ()):
            if prereq in by_target and by_target[prereq].step_id not in emitted:
                return False
        return True

    remaining = list(steps)
    emitted: set = set()
    ordered: List[HealingStep] = []

    guard = len(steps) * len(steps) + 1
    while remaining and guard > 0:
        guard -= 1
        # pilih langkah yang semua prereq-nya sudah emitted
        candidates = [s for s in remaining if target_ready(s, emitted)]
        if not candidates:
            # cycle: jatuh ke urutan priority (deterministik), tidak gagal
            remaining.sort(key=lambda s: (-s.priority, s.step_id))
            ordered.extend(remaining)
            emitted.update(s.step_id for s in remaining)
            remaining = []
            break
        # tie-break: priority turun, lalu step_id naik
        candidates.sort(key=lambda s: (-s.priority, s.step_id))
        pick = candidates[0]
        ordered.append(pick)
        emitted.add(pick.step_id)
        remaining.remove(pick)

    return ordered
