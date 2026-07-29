"""
OP-331 — Guardian Runtime V2

10-stage synchronous orchestration pipeline:
  collect_state → health → watchdog → policy → reasoning → decision →
  recommendation → audit → dashboard → conversation

Constraint:
  - No execution
  - No mission submit
  - No approval bypass
  - Read-only
  - Synchronous
  - Provider agnostic
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


# ══════════════════════════════════════════════════════════════════════
# DTOs
# ══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class StageResult:
    """Hasil satu stage pipeline."""
    stage: str
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0
    errors: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RuntimeV2Result:
    """Hasil akhir 10-stage pipeline."""
    pipeline_id: str
    success: bool
    stages: Tuple[StageResult, ...] = field(default_factory=tuple)
    started_at: str = ""
    completed_at: str = ""
    total_duration_ms: float = 0.0
    errors: Tuple[str, ...] = field(default_factory=tuple)
    pipeline_data: Dict[str, Any] = field(default_factory=dict)

    @property
    def stage_count(self) -> int:
        return len(self.stages)

    @property
    def failed_stages(self) -> List[str]:
        return [s.stage for s in self.stages if not s.success]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pipeline_id": self.pipeline_id,
            "success": self.success,
            "stage_count": self.stage_count,
            "failed_stages": self.failed_stages,
            "stages": [s.stage for s in self.stages],
            "total_duration_ms": self.total_duration_ms,
            "errors": list(self.errors),
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


# ── Parameter filter helpers ──

_HEALTH_PARAMS = {
    "reasoning_health", "provider_healthy", "provider_degraded",
    "provider_unhealthy", "approval_backlog", "audit_consistent",
    "trust_level", "queue_depth", "mission_active", "mission_capacity",
    "scheduler_overloaded",
}
_WATCHDOG_PARAMS = {
    "reasoning_sessions", "reasoning_max_duration_ms",
    "provider_errors", "approvals_stale_hours",
    "queue_depth", "queue_processed", "missions_stalled",
    "missions_active", "retry_count", "tasks_queued",
    "scheduler_capacity",
}
_POLICY_PARAMS = {
    "has_auto_execution", "has_approval", "has_conversation",
    "is_read_only", "has_evidence", "evidence_quality",
    "trust_level", "trust_threshold", "providers_healthy",
    "providers_total", "mission_active", "mission_max",
}
_SUPERVISOR_PARAMS = {
    "reasoning", "decision", "brain", "mission", "scheduler", "provider",
}
_SNAPSHOT_PARAMS = {
    "reasoning_sessions", "failure_count", "pending_approvals",
    "provider_healthy", "provider_degraded", "queue_depth",
    "pipeline_stage",
}


def _filter(d: Dict[str, Any], keys: set) -> Dict[str, Any]:
    return {k: v for k, v in d.items() if k in keys}


# ══════════════════════════════════════════════════════════════════════
# Pipeline
# ══════════════════════════════════════════════════════════════════════

class GuardianRuntimeV2:
    """10-stage orchestration pipeline — fully synchronous, read-only."""

    STAGES = (
        "collect_state", "health", "watchdog", "policy", "reasoning",
        "decision", "recommendation", "audit", "dashboard", "conversation",
    )

    def __init__(
        self,
        snapshot_engine: Any = None,
        health_engine: Any = None,
        watchdog: Any = None,
        policy_evaluator: Any = None,
        supervisor: Any = None,
        decision_service: Any = None,
        recommendation_engine: Any = None,
        audit: Any = None,
        dashboard_service: Any = None,
        conversation: Any = None,
        history: Any = None,
        trend: Any = None,
        summary: Any = None,
    ):
        self._snapshot_engine = snapshot_engine
        self._health_engine = health_engine
        self._watchdog = watchdog
        self._policy_evaluator = policy_evaluator
        self._supervisor = supervisor
        self._decision_service = decision_service
        self._recommendation_engine = recommendation_engine
        self._audit = audit
        self._dashboard_service = dashboard_service
        self._conversation = conversation
        self._history = history
        self._trend = trend
        self._summary = summary
        self._pipeline_count = 0
        self._results: List[RuntimeV2Result] = []

    # ── Properties ──

    @property
    def pipeline_count(self) -> int:
        return self._pipeline_count

    @property
    def results(self) -> Tuple[RuntimeV2Result, ...]:
        return tuple(self._results)

    @property
    def last_result(self) -> Optional[RuntimeV2Result]:
        return self._results[-1] if self._results else None

    @property
    def healthy(self) -> bool:
        last = self.last_result
        return last is not None and last.success

    # ── Run ──

    def run(self, **kwargs: Any) -> RuntimeV2Result:
        """Jalankan pipeline 10-stage. Kwargs difilter per stage."""
        started_at = datetime.now().isoformat(timespec="seconds")
        pipeline_id = "gv2-{}-{}".format(
            datetime.now().strftime("%H%M%S"), self._pipeline_count,
        )
        stage_results: List[StageResult] = []
        all_errors: List[str] = []
        pipeline_data: Dict[str, Any] = {}

        # Stage 1: collect_state
        sr = self._stage_collect_state(pipeline_data, kwargs)
        stage_results.append(sr)
        if not sr.success:
            all_errors.extend(sr.errors)

        # Stage 2: health
        sr = self._stage_health(pipeline_data, kwargs)
        stage_results.append(sr)
        if not sr.success:
            all_errors.extend(sr.errors)

        # Stage 3: watchdog
        sr = self._stage_watchdog(pipeline_data, kwargs)
        stage_results.append(sr)
        if not sr.success:
            all_errors.extend(sr.errors)

        # Stage 4: policy
        sr = self._stage_policy(pipeline_data, kwargs)
        stage_results.append(sr)
        if not sr.success:
            all_errors.extend(sr.errors)

        # Stage 5: reasoning
        sr = self._stage_reasoning(pipeline_data, kwargs)
        stage_results.append(sr)
        if not sr.success:
            all_errors.extend(sr.errors)

        # Stage 6: decision
        sr = self._stage_decision(pipeline_data, kwargs)
        stage_results.append(sr)
        if not sr.success:
            all_errors.extend(sr.errors)

        # Stage 7: recommendation
        sr = self._stage_recommendation(pipeline_data, kwargs)
        stage_results.append(sr)
        if not sr.success:
            all_errors.extend(sr.errors)

        # Stage 8: audit
        sr = self._stage_audit(pipeline_data, kwargs)
        stage_results.append(sr)
        if not sr.success:
            all_errors.extend(sr.errors)

        # Stage 9: dashboard
        sr = self._stage_dashboard(pipeline_data, kwargs)
        stage_results.append(sr)
        if not sr.success:
            all_errors.extend(sr.errors)

        # Stage 10: conversation
        sr = self._stage_conversation(pipeline_data, kwargs)
        stage_results.append(sr)
        if not sr.success:
            all_errors.extend(sr.errors)

        completed_at = datetime.now().isoformat(timespec="seconds")
        success = len(all_errors) == 0

        result = RuntimeV2Result(
            pipeline_id=pipeline_id,
            success=success,
            stages=tuple(stage_results),
            started_at=started_at,
            completed_at=completed_at,
            total_duration_ms=0.0,
            errors=tuple(all_errors),
            pipeline_data=pipeline_data,
        )

        self._pipeline_count += 1
        self._results.append(result)
        return result

    # ── Internal Stages ──

    def _stage_collect_state(self, data: Dict[str, Any], kw: Dict[str, Any]) -> StageResult:
        try:
            snapshot = None
            if self._snapshot_engine:
                snapshot = self._snapshot_engine.collect(**_filter(kw, _SNAPSHOT_PARAMS))
            data["state"] = snapshot.to_dict() if snapshot else {"status": "ok"}
            return StageResult(stage="collect_state", success=True, data={
                "snapshot_taken": snapshot is not None,
            })
        except Exception as e:
            return StageResult(stage="collect_state", success=False, errors=(str(e),))

    def _stage_health(self, data: Dict[str, Any], kw: Dict[str, Any]) -> StageResult:
        try:
            health = None
            if self._health_engine:
                health = self._health_engine.evaluate(**_filter(kw, _HEALTH_PARAMS))
            data["health"] = {
                "status": health.status if health else "unknown",
                "score": health.score.overall_score if health else 0.0,
            }
            return StageResult(stage="health", success=True, data={
                "status": health.status if health else "unknown",
            })
        except Exception as e:
            return StageResult(stage="health", success=False, errors=(str(e),))

    def _stage_watchdog(self, data: Dict[str, Any], kw: Dict[str, Any]) -> StageResult:
        try:
            if self._watchdog:
                wd_base = _filter(kw, _WATCHDOG_PARAMS)
                # Handler per function untuk passing params spesifik
                handle_fn = {
                    "check_stuck_reasoning": ("reasoning_sessions", "reasoning_max_duration_ms"),
                    "check_provider_timeout": ("provider_errors",),
                    "check_approval_deadlock": ("pending_approvals", "approvals_stale_hours"),
                    "check_queue_starvation": ("queue_depth", "queue_processed"),
                    "check_mission_stall": ("missions_stalled", "missions_active"),
                    "check_retry_loop": ("retry_count",),
                    "check_scheduler_overload": ("tasks_queued", "scheduler_capacity"),
                    "check_repeated_failures": ("failure_count",),
                }
                for check_fn, param_keys in handle_fn.items():
                    fn = getattr(self._watchdog, check_fn, None)
                    if fn:
                        fn(**_filter(kw, set(param_keys)))
            data["watchdog"] = {
                "alerts": len(self._watchdog.alerts) if self._watchdog else 0,
                "warnings": len(self._watchdog.warnings) if self._watchdog else 0,
            }
            return StageResult(stage="watchdog", success=True, data={
                "alerts": len(self._watchdog.alerts) if self._watchdog else 0,
            })
        except Exception as e:
            return StageResult(stage="watchdog", success=False, errors=(str(e),))

    def _stage_policy(self, data: Dict[str, Any], kw: Dict[str, Any]) -> StageResult:
        try:
            passed = True
            violations = 0
            if self._policy_evaluator:
                self._policy_evaluator.evaluate_all(**_filter(kw, _POLICY_PARAMS))
                passed = self._policy_evaluator.all_passed
                violations = len(self._policy_evaluator.violations)
            data["policy"] = {"passed": passed, "violations": violations}
            return StageResult(stage="policy", success=True, data={
                "passed": passed, "violations": violations,
            })
        except Exception as e:
            return StageResult(stage="policy", success=False, errors=(str(e),))

    def _stage_reasoning(self, data: Dict[str, Any], kw: Dict[str, Any]) -> StageResult:
        try:
            sessions = kw.get("reasoning_sessions", 0)
            failures = kw.get("failure_count", 0)
            if self._supervisor:
                self._supervisor.collect(**_filter(kw, _SUPERVISOR_PARAMS))
            data["reasoning"] = {"sessions": sessions, "failures": failures}
            return StageResult(stage="reasoning", success=True, data={
                "sessions": sessions, "failures": failures,
            })
        except Exception as e:
            return StageResult(stage="reasoning", success=False, errors=(str(e),))

    def _stage_decision(self, data: Dict[str, Any], kw: Dict[str, Any]) -> StageResult:
        try:
            pending = kw.get("pending_approvals", 0)
            data["decision"] = {"pending_approvals": pending}
            return StageResult(stage="decision", success=True, data={
                "pending_approvals": pending,
            })
        except Exception as e:
            return StageResult(stage="decision", success=False, errors=(str(e),))

    def _stage_recommendation(self, data: Dict[str, Any], kw: Dict[str, Any]) -> StageResult:
        try:
            recs = []
            if self._recommendation_engine:
                health_status = data.get("health", {}).get("status", "healthy")
                health_score = data.get("health", {}).get("score", 1.0)
                recs = self._recommendation_engine.aggregate(
                    health_status=health_status,
                    health_score=health_score,
                )
            data["recommendation"] = {"count": len(recs)}
            return StageResult(stage="recommendation", success=True, data={
                "count": len(recs),
            })
        except Exception as e:
            return StageResult(stage="recommendation", success=False, errors=(str(e),))

    def _stage_audit(self, data: Dict[str, Any], kw: Dict[str, Any]) -> StageResult:
        try:
            consistent = kw.get("audit_consistent", True)
            entries = 0
            if self._audit:
                entries = len(getattr(self._audit, "entries", []))
            data["audit"] = {"consistent": consistent, "entries": entries}
            return StageResult(stage="audit", success=True, data={
                "consistent": consistent, "entries": entries,
            })
        except Exception as e:
            return StageResult(stage="audit", success=False, errors=(str(e),))

    def _stage_dashboard(self, data: Dict[str, Any], kw: Dict[str, Any]) -> StageResult:
        try:
            dashboard = None
            if self._dashboard_service:
                dashboard = self._dashboard_service.get_dashboard()
            data["dashboard"] = {
                "generated": dashboard is not None,
                "overall_status": dashboard.overall_status if dashboard else "unknown",
            }
            return StageResult(stage="dashboard", success=True, data={
                "generated": dashboard is not None,
            })
        except Exception as e:
            return StageResult(stage="dashboard", success=False, errors=(str(e),))

    def _stage_conversation(self, data: Dict[str, Any], kw: Dict[str, Any]) -> StageResult:
        try:
            resp = None
            if self._conversation:
                resp = self._conversation.get_status()
            data["conversation"] = {
                "success": resp.success if resp else True,
            }
            return StageResult(stage="conversation", success=True, data={
                "success": resp.success if resp else True,
            })
        except Exception as e:
            return StageResult(stage="conversation", success=False, errors=(str(e),))
