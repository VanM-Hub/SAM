"""Mission Cognitive Runtime (MCR) — Cognitive Kernel / Program C (MISSION 4.6+).

Pure orchestrator. MCR TIDAK meniru OpenClaw, TIDAK meng-embed GPT, dan TIDAK
menjadi God Object. Ia hanya mengorkestrasi kemampuan SAM yang sudah ada
(foundation immutable) dan mewajibkan handoff governance ke kernel eksternal.

Alur satu siklus misi:
    Mission -> Reason -> Govern -> Execute -> Observe -> Reflect -> Learn

Prinsip yang dijaga (AD-ENG-001/002, AO-ENG-001):
- Foundational capability: ReasoningEngine = StructuredReasoningEngine (governed_reasoning).
- Governance WAJIB di level MCR. Authority tetap di Governance Kernel (eksternal).
- Observation read-only (Observe, never govern).
- Reflection memakai ReflectionManager healing (cycle_id/symptom/hypothesis/...).
- MCR memanggil capability; tidak mengganti atau menulis ulang apa pun.
"""
from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import structlog

# ── Foundational capabilities (panci B / existing) ──────────────────
from sam.governed_reasoning.structured_reasoning import (
    EvidenceRef,
    ReasoningStep,
    StructuredReasoning,
    StructuredReasoningEngine,
)
from sam.governed_reasoning.confidence_assessment import ConfidenceAssessor
from sam.observation.recommendation import ObservationRecommendationEngine
from sam.healing.reflection import ReflectionManager
from sam.agent.planner.mission_builder import MissionBuilder, PlanResult
from sam.execution_runtime.execution_request import ExecutionRequest


logger = structlog.get_logger()


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class MissionCycleStatus(str, Enum):
    CREATED = "created"
    REASONING = "reasoning"
    PLANNING = "planning"
    GOVERNANCE = "governance"
    EXECUTING = "executing"
    OBSERVING = "observing"
    REFLECTING = "reflecting"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"


@dataclass
class MissionCycleResult:
    """Hasil satu siklus misi — audit-friendly, tanpa authority."""

    cycle_id: str
    status: MissionCycleStatus
    mission: str
    reasoning_id: str = ""
    conclusion: str = ""
    plan_id: str = ""
    plan_step_count: int = 0
    plan_runtimes: tuple = ()  # urutan runtime pipeline dari MissionBuilder
    governance_decision: str = ""
    governance_reason: str = ""
    execution_summary: str = ""
    observation_summary: Any = None
    observation_available: bool = False
    reflection_id: str = ""
    lesson: str = ""
    error: str = ""
    created_at: str = field(default_factory=_now_utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "status": self.status.value,
            "mission": self.mission,
            "reasoning_id": self.reasoning_id,
            "conclusion": self.conclusion,
            "plan_id": self.plan_id,
            "plan_step_count": self.plan_step_count,
            "plan_runtimes": list(self.plan_runtimes),
            "governance_decision": self.governance_decision,
            "governance_reason": self.governance_reason,
            "execution_summary": self.execution_summary,
            "observation_summary": self.observation_summary,
            "observation_available": self.observation_available,
            "reflection_id": self.reflection_id,
            "lesson": self.lesson,
            "error": self.error,
            "created_at": self.created_at,
        }


def _default_reasoning_fn(
    context: Any, evidences: Tuple[EvidenceRef, ...]
) -> Tuple[List[ReasoningStep], str]:
    """Reasoning_fn bawaan berbasis evidence (mirip pola test panci B).

    Membuat premis dari tiap evidence, lalu menyimpulkan jumlah evidence.
    Dapat diganti caller lewat injeksi `reasoning_fn`.
    """
    steps: List[ReasoningStep] = []
    for i, ev in enumerate(evidences, start=1):
        steps.append(
            ReasoningStep(
                step_id=f"s{i}",
                kind="premise" if i < len(evidences) else "conclusion",
                content=f"observed {ev.evidence_id}",
                evidence_refs=(ev.evidence_id,),
            )
        )
    conclusion = "conclusion from " + str(len(evidences)) + " evidence"
    return steps, conclusion


class MissionCognitiveRuntime:
    """Orkestrator siklus kognitif misi.

    Pure orchestrator: memanggil ReasoningEngine (panci B), Governance Kernel
    (eksternal, wajib), Execution, Observation (read-only), ReflectionManager
    (healing). Tidak memiliki logic governance; tidak mengganti capability.
    """

    def __init__(
        self,
        reasoning_engine: Optional[StructuredReasoningEngine] = None,
        observation_engine: Optional[ObservationRecommendationEngine] = None,
        reflection_manager: Optional[ReflectionManager] = None,
        confidence_assessor: Optional[ConfidenceAssessor] = None,
        governance_engine: Any = None,
        execution_runtime: Any = None,
        execution_provider_id: str = "filesystem",
        execution_operation: str = "mission_execute",
        governance_required: bool = True,
        reasoning_fn: Optional[Any] = None,
        mission_builder: Optional[MissionBuilder] = None,
    ) -> None:
        self._reasoning_engine = reasoning_engine or StructuredReasoningEngine(
            reasoning_fn or _default_reasoning_fn
        )
        self._observation_engine = observation_engine
        self._reflection_manager = reflection_manager or ReflectionManager()
        self._confidence_assessor = confidence_assessor or ConfidenceAssessor()
        # Plan Construction HANYA via MissionBuilder — MCR tidak membuat plan sendiri.
        self._mission_builder = mission_builder or MissionBuilder()
        # Governance kernel EKSTERNAL — MCR tidak punya logic governance.
        self._governance_engine = governance_engine
        self._execution_runtime = execution_runtime
        # provider/operation di-pass dari wiring (DI), mode tetap preview (ADR-008).
        self._execution_provider_id = execution_provider_id
        self._execution_operation = execution_operation
        self._governance_required = governance_required
        self._last_lesson: str = ""
        self._logger = logger.bind(component="MissionCognitiveRuntime")

    # ── Public ──────────────────────────────────────────────────────────

    async def run_cycle(
        self,
        mission: str,
        evidences: Tuple[EvidenceRef, ...] = (),
        context: Optional[Dict[str, Any]] = None,
    ) -> MissionCycleResult:
        """Jalankan satu siklus misi penuh (reason->govern->execute->observe->reflect->learn)."""
        if not mission or not str(mission).strip():
            return self._fail(
                MissionCycleResult(cycle_id=_new_id("mc"), status=MissionCycleStatus.FAILED, mission=""),
                "mission is empty",
            )

        ctx = context or {}
        cycle_id = _new_id("mc")
        result = MissionCycleResult(
            cycle_id=cycle_id,
            status=MissionCycleStatus.CREATED,
            mission=mission,
        )
        self._logger.info("MCR cycle started", cycle_id=cycle_id, mission=mission)

        # 1) REASON ──────────────────────────────────────────────────────
        result.status = MissionCycleStatus.REASONING
        try:
            reasoning: StructuredReasoning = self._reasoning_engine.reason(
                question=mission, evidences=evidences, **ctx
            )
            result.reasoning_id = reasoning.reasoning_id
            result.conclusion = reasoning.conclusion
        except Exception as exc:  # pragma: no cover - defensive
            return self._fail(result, f"reasoning failed: {exc}")

        # 2) PLAN — Plan Construction HANYA via MissionBuilder (P3) ───────
        # MCR TIDAK membuat MissionPlan/MissionStep sendiri. Ia hanya invoke
        # MissionBuilder, consume structured plan, dan siapkan handoff ke
        # Governance. Gagal membangun plan = jalur terblokir (tidak mengeksekusi
        # dengan plan tidak valid).
        result.status = MissionCycleStatus.PLANNING
        if not self._build_plan(result, ctx):
            result.status = MissionCycleStatus.BLOCKED
            self._last_lesson = f"plan invalid: {result.error}"
            return result

        # 3) GOVERN (WAJIB — authority tetap eksternal) ───────────────────
        result.status = MissionCycleStatus.GOVERNANCE
        decision = await self._enforce_governance(result, ctx)
        if decision != "allow":
            result.governance_decision = decision
            result.status = MissionCycleStatus.BLOCKED
            self._last_lesson = f"governance blocked ({decision}): {result.governance_reason}"
            return result

        # 4) EXECUTE (serah ke jalur eksekusi resmi) ──────────────────────
        result.status = MissionCycleStatus.EXECUTING
        result.execution_summary = self._summarize_execution(cycle_id, mission, result.conclusion)
        self._logger.info("MCR governance allowed", cycle_id=cycle_id, decision=decision)

        # 5) OBSERVE (read-only, OPTIONAL/best-effort — T2) ───────────────
        # Observation TIDAK menggagalkan siklus (Observe, never govern / tanpa
        # authority, EA-C04/IP-3.2). Siklus tetap COMPLETED walau observasi
        # gagal; kegagalan dicatat via observation_available=False (auditable).
        result.status = MissionCycleStatus.OBSERVING
        result.observation_available, result.observation_summary = self._observe(
            cycle_id, mission
        )
        if not result.observation_available:
            self._logger.info(
                "MCR observation unavailable (best-effort, cycle proceeds)",
                cycle_id=cycle_id,
            )

        # 6) REFLECT + LEARN (best-effort) ────────────────────────────────
        result.status = MissionCycleStatus.REFLECTING
        await self._reflect(result, reasoning)

        result.status = MissionCycleStatus.COMPLETED
        result.lesson = self._last_lesson
        self._logger.info(
            "MCR cycle completed",
            cycle_id=cycle_id,
            status=result.status.value,
            lesson=result.lesson,
        )
        return result

    def get_last_lesson(self) -> str:
        """Lesson dari keputusan/siklus terakhir — untuk keputusan berikutnya."""
        return self._last_lesson

    # ── Planning (P3) — Plan Construction via MissionBuilder ─────────────

    def _build_plan(self, result: MissionCycleResult, ctx: Dict[str, Any]) -> bool:
        """Invoke MissionBuilder untuk membangun structured mission plan.

        MCR TIDAK membuat MissionPlan/MissionStep sendiri. Ia hanya memanggil
        MissionBuilder.build_default, consume hasilnya, dan menyiapkan summary
        yang auditable serta handoff ke governance. Gagal/plan invalid -> False
        (jalur terblokir, tidak dieksekusi).
        """
        mission_id = str(ctx.get("mission_id", "mcr")) if isinstance(ctx, dict) else "mcr"
        plan_id = f"plan-{result.cycle_id}"
        try:
            plan_result: PlanResult = self._mission_builder.build_default(
                plan_id, mission_id
            )
        except Exception as exc:  # pragma: no cover - defensive
            result.error = f"plan construction failed: {exc}"
            return False
        if not plan_result.valid or plan_result.plan is None:
            result.error = "mission plan invalid"
            return False
        plan = plan_result.plan
        runtimes = tuple(
            getattr(s, "runtime_name", "") for s in getattr(plan, "steps", []) or []
        )
        result.plan_id = plan_id
        result.plan_step_count = len(runtimes)
        result.plan_runtimes = runtimes
        self._logger.info(
            "MCR plan built via MissionBuilder",
            cycle_id=result.cycle_id,
            plan_id=plan_id,
            step_count=result.plan_step_count,
        )
        return True

    # ── Governance (handoff WAJIB, authority eksternal) ─────────────────

    async def _enforce_governance(
        self, result: MissionCycleResult, ctx: Dict[str, Any]
    ) -> str:
        """Meminta keputusan ke Governance Kernel eksternal.

        MCR TIDAK memiliki logic governance. Ia menyerahkan graph + konteks ke
        governance_engine; kewenangan tetap di kernel eksternal.
        """
        if self._governance_engine is None:
            if self._governance_required:
                result.governance_reason = (
                    "governance engine required but not provided (MCR enforces governance)"
                )
                return "blocked"
            # dev/ops mode: dibolehkan hanya untuk pengujian, bukan produksi.
            return "allow"

        try:
            graph = self._build_decision_graph(result, ctx)
            if asyncio.iscoroutinefunction(self._governance_engine.evaluate):
                verdict = await self._governance_engine.evaluate(graph, {})
            else:
                verdict = self._governance_engine.evaluate(graph, {})
        except Exception as exc:  # pragma: no cover - defensive
            result.governance_reason = f"governance evaluation error: {exc}"
            return "error"

        decision = getattr(verdict, "decision", verdict)
        result.governance_decision = str(decision)
        result.governance_reason = str(getattr(verdict, "reason", ""))
        return str(decision)

    def _build_decision_graph(self, result: MissionCycleResult, ctx: Dict[str, Any]) -> Any:
        """Membangun representasi keputusan untuk governance kernel.

        Termasuk handoff plan (dari MissionBuilder) agar governance menilai
        keputusan dengan konteks rencana yang diusulkan. Kontrak longgar (dict)
        agar tidak terikat ke tipe plugin tertentu.
        """
        return {
            "cycle_id": result.cycle_id,
            "mission": result.mission,
            "reasoning_id": result.reasoning_id,
            "conclusion": result.conclusion,
            "plan": {
                "plan_id": result.plan_id,
                "step_count": result.plan_step_count,
                "runtimes": list(result.plan_runtimes),
            },
            "context": ctx,
        }

    # ── Execution (serah ke jalur resmi — ADR-008 Real Execution Runtime) ──

    def _summarize_execution(
        self, cycle_id: str, mission: str, conclusion: str
    ) -> str:
        """Serah eksekusi ke jalur resmi (ExecutionRuntime / ExecutionEngine).

        T3 (keputusan CA): MCR TIDAK mengeksekusi sendiri dan TIDAK memanggil
        method khayalan. Ia membangun `ExecutionRequest` (mode='preview', ADR-008
        section 12: provider TIDAK dieksekusi, external_calls=0) dan menyerahkan
        ke jalur resmi lewat `execute(request)` (ExecutionEngine) atau
        `run(runtime_id, request)` (ExecutionRuntime).

        Jika execution engine tersedia tapi TIDAK punya method resmi, MCR mencatat
        eksplisit "no-execution-method" (bukan silent no-op) dan TIDAK berpura-
        pura mengeksekusi (bukan God Object).
        """
        summary = f"instruction:{mission} | conclusion:{conclusion}"
        if self._execution_runtime is None:
            return summary

        # Bangun request resmi (immutable, preview-only sesuai ADR-008):
        request = ExecutionRequest(
            execution_id=f"mc-{cycle_id}",
            provider_id=self._execution_provider_id,
            operation=self._execution_operation,
            mode="preview",  # ADR-008 sec 12: provider tidak dieksekusi
            payload={
                "mission": mission,
                "conclusion": conclusion,
                "cycle_id": cycle_id,
            },
        )
        try:
            execute = getattr(self._execution_runtime, "execute", None)
            run = getattr(self._execution_runtime, "run", None)
            if callable(execute):
                outcome = execute(request)
            elif callable(run):
                outcome = run(f"mc-{cycle_id}-run", request)
            else:
                # engine ada tapi tak punya method resmi -> tandai (bukan silent)
                summary = f"{summary} | no-execution-method"
                return summary
            # Ringkas hasil (ExecutionOutcome / ExecutionResponse-like):
            if hasattr(outcome, "as_dict"):
                summary = f"{summary} | result:{outcome.as_dict()}"
            else:
                summary = f"{summary} | result:{outcome}"
        except Exception as exc:  # pragma: no cover - defensive
            summary = f"{summary} | execute-error:{exc}"
        return summary

    # ── Observation (read-only, best-effort / OPTIONAL — T2) ─────────────

    def _observe(self, cycle_id: str, mission: str) -> Tuple[bool, Any]:
        """Mengamati hasil via ObservationRecommendationEngine (read-only).

        T2 (keputusan CA): Observation bersifat OPTIONAL (best-effort) mengikuti
        prinsip "Observe, never govern" + "tanpa authority" (EA-C04, IP-3.2).
        Gagal/tanpa engine TIDAK menggagalkan siklus — siklus tetap COMPLETED.
        Namun kegagalan dicatat eksplisit lewat flag `available` agar auditable
        (bukan diam-diam None). Return (available: bool, summary: Any).
        """
        if self._observation_engine is None:
            return False, None
        try:
            # ObservationRecommendationEngine menyediakan `recommend()` (read-only),
            # bukan `observe()`. Panggil method yang benar sesuai kontrak panci B.
            recom = self._observation_engine.recommend()
            # Selalu ratakan jadi dict agar auditable & konsisten dengan to_dict().
            if isinstance(recom, dict):
                return True, recom
            if hasattr(recom, "as_dict"):
                return True, recom.as_dict()
            if hasattr(recom, "to_dict"):
                return True, recom.to_dict()
            if hasattr(recom, "__dict__"):
                return True, vars(recom)
            return True, str(recom)
        except Exception:  # pragma: no cover - defensive
            return False, None

    # ── Reflection + Learning (reuse ReflectionManager healing) ─────────

    async def _reflect(self, result: MissionCycleResult,
                       reasoning: Optional[StructuredReasoning] = None) -> None:
        """Merekam refleksi memakai ReflectionManager healing.

        Memakai semantik healing (cycle_id/symptom/hypothesis/action_taken/
        gap_analysis). Gagal refleksi TIDAK menggagalkan siklus (best-effort).

        `reasoning` (objek StructuredReasoning) diteruskan ke confidence assessor
        agar cocok dengan kontrak assessor yang membutuhkan objek reasoning,
        bukan string conclusion (lihat T1).
        """
        try:
            # pastikan SEMUA field str (ReflectionRecord=extra forbid, butuh str bukan None)
            obs_str = result.observation_summary
            if obs_str is None:
                obs_str = ""
            else:
                obs_str = str(obs_str)
            record = await self._reflection_manager.record_reflection(
                cycle_id=result.cycle_id,
                symptom=str(result.observation_summary or result.execution_summary or ""),
                hypothesis=str(result.conclusion or ""),
                action_taken=f"execute:{result.execution_summary}",
                expected_outcome=f"govern:{result.governance_decision}",
                actual_outcome=obs_str,
                gap_analysis="",
                lessons=[result.lesson] if result.lesson else [],
                confidence=await self._assess_confidence(result, reasoning),
                success=(result.status is MissionCycleStatus.COMPLETED),
                metadata={"mission": result.mission},
            )
            result.reflection_id = record.id
        except Exception as exc:  # pragma: no cover - defensive
            self._logger.warning("MCR reflection skipped", cycle_id=result.cycle_id, error=str(exc))

    async def _assess_confidence(
        self,
        result: MissionCycleResult,
        reasoning: Optional[StructuredReasoning] = None,
    ) -> float:
        """Menilai confidence sesuai kontrak ConfidenceAssessor (T1).

        Assessor (governed_reasoning) membutuhkan objek `StructuredReasoning`,
        bukan string conclusion. Sebelum T1, MCR memanggil assess(benar, salah)
        dengan 2 arg sehingga selalu dicegat except -> confidence 0.0 (silent).
        Setelah T1: MCR meneruskan objek reasoning & membaca atribut `value`.
        """
        try:
            assert reasoning is not None, "reasoning required for confidence assessment"
            assessment = self._confidence_assessor.assess(reasoning)
            return float(getattr(assessment, "value", 0.0) or 0.0)
        except Exception:  # pragma: no cover - defensive
            return 0.0

    def _fail(self, result: MissionCycleResult, error: str) -> MissionCycleResult:
        result.status = MissionCycleStatus.FAILED
        result.error = error
        self._last_lesson = f"cycle failed: {error}"
        self._logger.error("MCR cycle failed", cycle_id=result.cycle_id, error=error)
        return result


__all__ = [
    "MissionCognitiveRuntime",
    "MissionCycleResult",
    "MissionCycleStatus",
]
