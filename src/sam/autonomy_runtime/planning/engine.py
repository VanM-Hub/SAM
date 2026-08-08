# Runtime Planning Engine - WP-12
# IP-3.2-002 (AO-3.2-001 / ED-3.2-002)
#
# Deterministic operational plan dari observation & diagnostics.
# Menerima kondisi runtime (observasi + diagnostik) dan menghasilkan RuntimePlan
# (urutan kerja proposal) secara DETERMINISTIK - tanpa AI/LLM, tanpa aksi,
# tanpa keputusan konstitusional. Prinsip: Plan, never decide.

from typing import Dict, List, Optional, Tuple

from sam.autonomy_runtime.planning.models import (
    PlanStep,
    PlanningContext,
    PlanningMetadata,
    RuntimePlan,
)

# Kandidat aksi proposional per kondisi komponen (LABEL, bukan eksekusi).
# action diawali "plan_" menandakan ini hanya ide kerja yang diusulkan.
_ACTION_BY_CONDITION = {
    "unhealthy": "plan_repair_or_recover",
    "degraded": "plan_optimize",
    "unknown": "plan_verify",
    "unavailable": "plan_restore_availability",
}

# Prioritas default per kondisi (semakin tinggi = semakin dulu diusulkan).
_PRIORITY_BY_CONDITION = {
    "unhealthy": 3,
    "unavailable": 3,
    "degraded": 2,
    "unknown": 1,
    "healthy": 0,
}


class PlanningEngine:
    """Menghasilkan rencana operasional deterministik dari kondisi runtime."""

    def __init__(self) -> None:
        pass

    def build_plan(
        self,
        context: PlanningContext,
        plan_id: Optional[str] = None,
        created_at: str = "",
        evidence_refs: Optional[Tuple[str, ...]] = None,
    ) -> RuntimePlan:
        """Bangun RuntimePlan dari PlanningContext (deterministik)."""
        steps = self._build_steps(context)
        steps = self._sort_steps(steps)
        pid = plan_id or "plan-{}".format(_stable_seed(context))
        meta = PlanningMetadata(
            plan_id=pid,
            created_at=created_at,
            basis=_basis_description(context),
            evidence_refs=tuple(evidence_refs or ()),
        )
        summary = _summarize(context, steps)
        state = _plan_state(context)
        return RuntimePlan(
            plan_id=pid,
            context=context,
            metadata=meta,
            steps=steps,
            created_at=created_at,
            state=state,
            summary=summary,
        )

    # --- internal ---

    def _build_steps(self, context: PlanningContext) -> Tuple[PlanStep, ...]:
        """Buat satu PlanStep per komponen yang butuh perhatian, deterministik."""
        steps: List[PlanStep] = []
        counter = 0
        for target in self._ordered_targets(context):
            condition = self._condition_of(context, target)
            if condition in ("healthy", "none"):
                continue
            counter += 1
            action = _ACTION_BY_CONDITION.get(condition, "plan_verify")
            prereqs = self._prereqs_of(context, target)
            steps.append(PlanStep(
                step_id="step-{}".format(counter),
                action=action,
                target=target,
                prerequisite_ids=prereqs,
                readiness_gate=condition,
                priority=_PRIORITY_BY_CONDITION.get(condition, 1),
                reason=_reason_for(context, target, condition),
            ))
        return tuple(steps)

    def _ordered_targets(self, context: PlanningContext) -> List[str]:
        """Urutan target: unavailable > degraded > healthy, per metadata order."""
        order: List[str] = []
        for name in context.unavailable_components:
            if name not in order:
                order.append(name)
        for name in context.degraded_components:
            if name not in order:
                order.append(name)
        for name in context.healthy_components:
            if name not in order:
                order.append(name)
        # edge target yang disebut di dependency ikut dimasukkan bila belum
        for src, dst in context.dependency_edges:
            for n in (src, dst):
                if n not in order:
                    order.append(n)
        return order

    def _condition_of(self, context: PlanningContext, target: str) -> str:
        if target in context.unavailable_components:
            return "unavailable"
        if target in context.degraded_components:
            return "degraded"
        if target in context.healthy_components:
            return "healthy"
        # tidak terdaftar eksplisit -> cek dependency edge sebagai unknown
        return "unknown"

    def _prereqs_of(self, context: PlanningContext, target: str) -> Tuple[str, ...]:
        """Prasyarat target: komponen yang harus siap sebelum target (dependency).

        Mencatat dependency ASLI dari dependency graph - semua komponen yang
        menjadi prasyarat target, terlepas dari statusnya saat ini. Penilaian
        "apakah prereq tersedia" adalah domain SchedulingEngine (WP-14),
        bukan perekam dependency ini. Ini menjaga dependency-aware sequencing
        tetap benar walau beberapa komponen tidak sehat.
        """
        prereqs: List[str] = []
        for src, dst in context.dependency_edges:
            if dst == target and src not in prereqs:
                prereqs.append(src)
        return tuple(prereqs)

    def _sort_steps(self, steps: Tuple[PlanStep, ...]) -> Tuple[PlanStep, ...]:
        """Urutkan langkah: priority turun, lalu step_id naik (deterministik)."""
        return tuple(sorted(steps, key=lambda s: (-s.priority, s.step_id)))


def _stable_seed(context: PlanningContext) -> str:
    """Seed deterministik dari isi context (tanpa random)."""
    parts = [
        context.source,
        context.overall_health,
        context.readiness_level,
        "_".join(context.unavailable_components),
        "_".join(context.degraded_components),
        "_".join(sorted(_edge_str(e) for e in context.dependency_edges)),
    ]
    raw = "|".join(parts)
    return _sha(raw)


def _edge_str(edge: Tuple[str, str]) -> str:
    return "{}>{}".format(edge[0], edge[1])


def _sha(text: str) -> str:
    import hashlib
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:8]


def _basis_description(context: PlanningContext) -> str:
    return "observation+diagnostics health={} readiness={}".format(
        context.overall_health, context.readiness_level
    )


def _reason_for(
    context: PlanningContext, target: str, condition: str
) -> str:
    """Alasan observasional deterministik utk target pada kondisi tertentu."""
    if condition in ("unhealthy", "unavailable"):
        return "{} is {}; propose repair/recovery as a plan (no action)".format(
            target, condition
        )
    if condition == "degraded":
        return "{} is degraded; propose optimization (no action)".format(target)
    if condition == "unknown":
        return "{} status unknown; propose verification (no action)".format(target)
    return "{}".format(target)


def _summarize(context: PlanningContext, steps: Tuple[PlanStep, ...]) -> str:
    if not steps:
        return "no operational proposals - runtime is healthy"
    return "{} proposal(s) for runtime readiness={}".format(
        len(steps), context.readiness_level
    )


def _plan_state(context: PlanningContext) -> str:
    if context.readiness_level == "ready":
        return "ready"
    if context.readiness_level in ("degraded", "not_ready", "unknown"):
        return "blocked"
    return "proposed"
