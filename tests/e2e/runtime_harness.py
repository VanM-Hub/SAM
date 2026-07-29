"""
OP-351 — End-to-End Runtime Harness

Menjalankan pipeline SAM lengkap dengan modul sebenarnya.
Tidak menggunakan mock.
Hanya synchronous, read-only, tidak auto-execute, tidak auto-approve.

Pipeline:
  Guardian_v2 → Governance → Readiness → Risk → Explanation → Dashboard
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


# ──────────────────────────────────────────────────────────────
# Stage Result DTOs
# ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class StageResult:
    stage: str
    success: bool
    duration_ms: float
    output: Any = None
    error: Optional[str] = None
    evidence: Tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "success": self.success,
            "duration_ms": round(self.duration_ms, 2),
            "error": self.error,
            "evidence_count": len(self.evidence),
        }


@dataclass(frozen=True)
class PipelineRun:
    run_id: str
    scenario: str
    timestamp: str
    total_duration_ms: float
    stages: Tuple[StageResult, ...]
    all_passed: bool
    total_evidence: int
    scenario_data: Dict[str, Any] = field(default_factory=dict)
    governance_passed: Optional[bool] = None
    readiness_passed: Optional[bool] = None
    risk_safe: Optional[bool] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "scenario": self.scenario,
            "total_duration_ms": round(self.total_duration_ms, 2),
            "all_passed": self.all_passed,
            "total_evidence": self.total_evidence,
            "governance_passed": self.governance_passed,
            "readiness_passed": self.readiness_passed,
            "risk_safe": self.risk_safe,
            "stages": [s.to_dict() for s in self.stages],
        }


# ──────────────────────────────────────────────────────────────
# Runtime Harness
# ──────────────────────────────────────────────────────────────

class RuntimeHarness:
    """End-to-end runtime harness — jalankan pipeline dengan modul sebenarnya."""

    def __init__(self, scenario: str = "default"):
        self._scenario = scenario
        self._run_count = 0
        self._last_run: Optional[PipelineRun] = None
        self._engines: Dict[str, Any] = {}

    def _load_engine(self, name: str) -> Any:
        if name in self._engines:
            return self._engines[name]
        engine = None
        if name == "observation":
            from sam.operations.brain.observation_engine import ObservationEngine
            engine = ObservationEngine()
        elif name == "reasoning":
            from sam.operations.brain.reasoning.pipeline import ReasoningPipeline
            engine = ReasoningPipeline()
        elif name == "decision":
            from sam.operations.brain.decision.evaluator import DecisionEvaluator
            engine = DecisionEvaluator()
        elif name == "guardian":
            from sam.operations.brain.guardian.runtime import GuardianRuntime
            engine = GuardianRuntime()
        elif name == "guardian_v2":
            from sam.operations.brain.guardian.runtime_v2 import GuardianRuntimeV2
            engine = GuardianRuntimeV2()
        elif name == "governance":
            from sam.operations.brain.guardian import GuardianGovernanceEngine
            engine = GuardianGovernanceEngine()
        elif name == "readiness":
            from sam.operations.brain.guardian import ExecutionReadinessEvaluator
            engine = ExecutionReadinessEvaluator()
        elif name == "risk":
            from sam.operations.brain.guardian import GuardianRiskAssessment
            engine = GuardianRiskAssessment()
        elif name == "explanation":
            from sam.operations.brain.guardian import GuardianDecisionExplanation
            engine = GuardianDecisionExplanation()
        elif name == "coordination":
            from sam.operations.brain.guardian import GuardianCoordinationRuntime
            engine = GuardianCoordinationRuntime()
        elif name == "conversation_governance":
            from sam.operations.brain.guardian import GovernanceConversationBridge
            engine = GovernanceConversationBridge()
        elif name == "dashboard_v2":
            from sam.operations.brain.guardian.dashboard_v2 import GuardianDashboardV2Service
            engine = GuardianDashboardV2Service()
        elif name == "dashboard_v3":
            from sam.operations.brain.guardian import GuardianDashboardV3Service
            engine = GuardianDashboardV3Service()
        elif name == "conversation_v2":
            from sam.operations.brain.guardian.conversation_v2 import GuardianConversationV2
            engine = GuardianConversationV2()
        elif name == "routing_v2":
            from sam.operations.brain.guardian.routing_v2 import GuardianRoutingV2Integration
            engine = GuardianRoutingV2Integration()
        elif name == "snapshot":
            from sam.operations.brain.guardian.snapshot import GuardianSnapshotEngine
            engine = GuardianSnapshotEngine()
        elif name == "history":
            from sam.operations.brain.guardian.history import GuardianHistoryService
            engine = GuardianHistoryService()
        elif name == "trend":
            from sam.operations.brain.guardian.trend import GuardianTrendAnalyzer
            engine = GuardianTrendAnalyzer()
        elif name == "summary":
            from sam.operations.brain.guardian.summary import GuardianSummaryBuilder
            engine = GuardianSummaryBuilder()
        elif name == "runtime_supervisory":
            from sam.operations.brain.guardian.runtime_supervisory import GuardianSupervisoryRuntime
            engine = GuardianSupervisoryRuntime()
        elif name == "integration_v2":
            from sam.operations.brain.integration_v2 import IntegrationV2
            engine = IntegrationV2()
        else:
            raise ValueError(f"Unknown engine: {name}")

        self._engines[name] = engine
        return engine

    def set_engine(self, name: str, engine: Any) -> None:
        self._engines[name] = engine

    def _run_stage(self, name: str, method: str, params: dict) -> StageResult:
        t0 = datetime.now()
        error: Optional[str] = None
        output = None
        evidence: List[str] = []

        try:
            engine = self._load_engine(name)
            fn = getattr(engine, method)
            output = fn(**params)
            evidence.append(f"{name}.{method}() completed")
        except Exception as e:
            try:
                error = f"{type(e).__name__}: {e}"
            except UnicodeEncodeError:
                error = f"{type(e).__name__}: (unicode content)"

        dur = (datetime.now() - t0).total_seconds() * 1000
        return StageResult(
            stage=name,
            success=error is None,
            duration_ms=dur,
            output=output,
            error=error,
            evidence=tuple(evidence),
        )

    def _get_semantic(self, stage_result: StageResult, attr: str):
        """Ambil atribut dari output stage."""
        if stage_result.success and stage_result.output:
            return getattr(stage_result.output, attr, None)
        return None

    def run_governance_pipeline(self, **kw: Any) -> PipelineRun:
        t0 = datetime.now()
        stages: List[StageResult] = []

        stages.append(self._run_stage("governance", "evaluate", kw))
        stages.append(self._run_stage("readiness", "evaluate", kw))
        stages.append(self._run_stage("risk", "assess", kw))
        stages.append(self._run_stage("explanation", "build", kw))
        stages.append(self._run_stage("conversation_governance", "query",
                                       {"query_type": "governance_report", **kw}))

        total_evidence = sum(len(s.evidence) for s in stages)
        dur = (datetime.now() - t0).total_seconds() * 1000
        run_id = f"gov-{self._run_count}-{datetime.now().strftime('%H%M%S')}"
        self._run_count += 1

        pr = PipelineRun(
            run_id=run_id,
            scenario=self._scenario,
            timestamp=datetime.now().isoformat(timespec="seconds"),
            total_duration_ms=dur,
            stages=tuple(stages),
            all_passed=all(s.success for s in stages),
            total_evidence=total_evidence,
            scenario_data=dict(kw),
            governance_passed=self._get_semantic(stages[0], "approved"),
            readiness_passed=self._get_semantic(stages[1], "ready"),
            risk_safe=self._get_semantic(stages[2], "is_safe"),
        )
        self._last_run = pr
        return pr

    def run_full_pipeline(self, **kw: Any) -> PipelineRun:
        t0 = datetime.now()
        stages: List[StageResult] = []

        # Stage 1: Guardian Runtime V2
        stages.append(self._run_stage("guardian_v2", "run", kw))

        # Stage 2: Governance — filter params
        gov_params = {k: v for k, v in kw.items() if k in (
            "policy_passed", "policy_violations",
            "health_status", "health_score",
            "decision_approved", "decision_confidence",
            "approval_complete", "approval_required", "approval_granted",
            "recommendation_support", "recommendation_risk",
        )}
        stages.append(self._run_stage("governance", "evaluate", gov_params))

        # Stage 3: Readiness — filter params
        ready_params = {k: v for k, v in kw.items() if k in (
            "approval_complete", "approval_rate",
            "policy_passed", "policy_violations",
            "confidence_score", "confidence_threshold",
            "evidence_count", "evidence_minimum",
            "guardian_healthy", "guardian_score",
            "conflict_detected", "conflict_count",
            "dependency_complete", "dependency_pending",
        )}
        stages.append(self._run_stage("readiness", "evaluate", ready_params))

        # Stage 4: Risk — filter params
        risk_params = {k: v for k, v in kw.items() if k in (
            "system_health", "health_score",
            "policy_violations", "policy_score",
            "execution_complexity", "execution_failures",
            "dependency_pending", "dependency_count",
            "approval_missing", "approval_required",
            "confidence_score", "evidence_quality",
        )}
        stages.append(self._run_stage("risk", "assess", risk_params))

        # Stage 5: Explanation — gunakan defaults dari actual governance/readiness/risk
        expl_params = dict(kw)
        # Ambil dari stage sebelumnya jika ada output
        gov_result = stages[1].output if len(stages) > 1 and stages[1].success else None
        ready_result = stages[2].output if len(stages) > 2 and stages[2].success else None
        risk_result = stages[3].output if len(stages) > 3 and stages[3].success else None
        if isinstance(gov_result, dict) and "overall_status" in gov_result:
            expl_params.setdefault("governance_status", gov_result.get("overall_status"))
            expl_params.setdefault("governance_score", gov_result.get("overall_score"))
        if isinstance(ready_result, dict) and "overall_level" in ready_result:
            expl_params.setdefault("readiness_level", ready_result.get("overall_level"))
            expl_params.setdefault("readiness_score", ready_result.get("overall_score"))
        if isinstance(risk_result, dict) and "overall_level" in risk_result:
            expl_params.setdefault("risk_level", risk_result.get("overall_level"))
            expl_params.setdefault("risk_score", risk_result.get("overall_score"))
        stages.append(self._run_stage("explanation", "build", expl_params))

        # Stage 6: Dashboard V3
        stages.append(self._run_stage("dashboard_v3", "build_governance_card",
                                       gov_params))

        total_evidence = sum(len(s.evidence) for s in stages)
        dur = (datetime.now() - t0).total_seconds() * 1000
        run_id = f"full-{self._run_count}-{datetime.now().strftime('%H%M%S')}"
        self._run_count += 1

        pr = PipelineRun(
            run_id=run_id,
            scenario=self._scenario,
            timestamp=datetime.now().isoformat(timespec="seconds"),
            total_duration_ms=dur,
            stages=tuple(stages),
            all_passed=all(s.success for s in stages),
            total_evidence=total_evidence,
            scenario_data=dict(kw),
            governance_passed=self._get_semantic(stages[1], "approved"),
            readiness_passed=self._get_semantic(stages[2], "ready"),
            risk_safe=self._get_semantic(stages[3], "is_safe"),
        )
        self._last_run = pr
        return pr

    @property
    def run_count(self) -> int:
        return self._run_count

    @property
    def last_run(self) -> Optional[PipelineRun]:
        return self._last_run

    def summary(self) -> str:
        if not self._last_run:
            return "No runs yet"
        r = self._last_run
        lines = [
            f"Run {r.run_id} — {r.scenario}",
            f"  Duration: {r.total_duration_ms:.1f}ms",
            f"  All stages OK: {r.all_passed}",
            f"  Governance passed: {r.governance_passed}",
            f"  Readiness passed: {r.readiness_passed}",
            f"  Risk safe: {r.risk_safe}",
            f"  Total evidence: {r.total_evidence}",
        ]
        for s in r.stages:
            ok = "\u2705" if s.success else "\u274c"
            lines.append(f"  {ok} {s.stage}: {s.duration_ms:.1f}ms")
        return "\n".join(lines)
