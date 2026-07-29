"""
OP-328 — Guardian Runtime Integration

Hubungkan:
  Observation → Brain → Reasoning → Decision → Guardian Supervisor → Conversation → Dashboard

Pipeline hanya sinkron.
Tidak boleh ada thread.
Tidak boleh background task.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


@dataclass(frozen=True)
class SupervisoryPipelineResult:
    pipeline_id: str
    observation_ok: bool = False
    brain_ok: bool = False
    reasoning_ok: bool = False
    decision_ok: bool = False
    supervisor_ok: bool = False
    conversation_ok: bool = False
    dashboard_ok: bool = False
    success: bool = False
    errors: Tuple[str, ...] = ()
    started_at: str = ""
    completed_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pipeline_id": self.pipeline_id,
            "success": self.success,
            "stages": {
                "observation": self.observation_ok,
                "brain": self.brain_ok,
                "reasoning": self.reasoning_ok,
                "decision": self.decision_ok,
                "supervisor": self.supervisor_ok,
                "conversation": self.conversation_ok,
                "dashboard": self.dashboard_ok,
            },
            "errors": list(self.errors),
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


class GuardianSupervisoryRuntimeIntegration:
    """
    Pipeline integrasi untuk Guardian Supervisor.

    Menghubungkan:
      Observation → Brain → Reasoning → Decision → Supervisor → Conversation → Dashboard

    Synchronous-only. No threading.
    """

    def __init__(
        self,
        supervisor: Any,
        health_engine: Any,
        watchdog: Any,
        policy_evaluator: Any,
        recommendation_engine: Any,
        conversation: Any,
        dashboard_service: Any,
    ) -> None:
        self._supervisor = supervisor
        self._health = health_engine
        self._watchdog = watchdog
        self._policy = policy_evaluator
        self._recommendation = recommendation_engine
        self._conversation = conversation
        self._dashboard = dashboard_service
        self._pipeline_count: int = 0
        self._results: List[SupervisoryPipelineResult] = []

    def run(
        self,
        observation_ok: bool = True,
        brain_ok: bool = True,
        reasoning_ok: bool = True,
        reasoning_sessions: int = 0,
        reasoning_max_duration_ms: float = 0.0,
        decision_ok: bool = True,
        pending_approvals: int = 0,
        approvals_stale_hours: float = 0.0,
        provider_healthy: int = 1,
        provider_degraded: int = 0,
        provider_errors: int = 0,
        trust_level: float = 1.0,
        queue_depth: int = 0,
        queue_processed: int = 0,
        missions_active: int = 0,
        missions_stalled: int = 0,
        retry_count: int = 0,
        tasks_queued: int = 0,
        failure_count: int = 0,
        audit_consistent: bool = True,
        evidence_quality: float = 1.0,
        has_auto_execution: bool = False,
        has_approval: bool = True,
        has_conversation: bool = True,
        has_evidence: bool = True,
        is_read_only: bool = True,
    ) -> SupervisoryPipelineResult:
        pid = "sp-{}-{}".format(
            datetime.now().strftime("%H%M%S"), self._pipeline_count
        )
        self._pipeline_count += 1
        started = datetime.now().isoformat(timespec="seconds")
        errors: List[str] = []

        # Stage 1: Observation
        if not observation_ok:
            errors.append("Observation failed")

        # Stage 2: Brain
        if not brain_ok:
            errors.append("Brain pipeline failed")

        # Stage 3: Reasoning
        if not reasoning_ok:
            errors.append("Reasoning failed")

        # Stage 4: Decision
        if not decision_ok:
            errors.append("Decision failed")

        # Stage 5: Guardian Supervisor
        try:
            from .supervisor import ReasoningStatus, DecisionStatus, BrainStatus, \
                MissionStatus, SchedulerStatus, ProviderStatus

            snapshot = self._supervisor.collect(
                reasoning=ReasoningStatus(
                    active_sessions=reasoning_sessions,
                    failed_count=failure_count,
                ),
                decision=DecisionStatus(
                    total_decisions=0,
                    pending_approvals=pending_approvals,
                ),
                brain=BrainStatus(
                    pipeline_active=brain_ok,
                    error_count=failure_count,
                ),
                mission=MissionStatus(
                    active_missions=missions_active,
                    stalled_missions=missions_stalled,
                ),
                scheduler=SchedulerStatus(
                    tasks_queued=tasks_queued,
                    tasks_running=0,
                ),
                provider=ProviderStatus(
                    active_providers=provider_healthy + provider_degraded,
                    healthy_providers=provider_healthy,
                    degraded_providers=provider_degraded,
                ),
            )
        except Exception as e:
            errors.append("Supervisor error: {}".format(e))

        # Stage 5b: Health
        try:
            self._health.evaluate(
                reasoning_ok=reasoning_ok,
                provider_healthy=provider_healthy,
                provider_degraded=provider_degraded,
                approval_backlog=pending_approvals,
                audit_consistent=audit_consistent,
                trust_level=trust_level,
                queue_depth=queue_depth,
                mission_active=missions_active,
                scheduler_overloaded=(tasks_queued > 100),
                total_reasoning_failures=failure_count,
            )
        except Exception as e:
            errors.append("Health error: {}".format(e))

        # Stage 5c: Watchdog
        try:
            self._watchdog.run_all(
                reasoning_sessions=reasoning_sessions,
                reasoning_max_duration_ms=reasoning_max_duration_ms,
                provider_errors=provider_errors,
                pending_approvals=pending_approvals,
                stale_hours=approvals_stale_hours,
                queue_depth=queue_depth,
                queue_processed=queue_processed,
                stalled_missions=missions_stalled,
                active_missions=missions_active,
                retry_count=retry_count,
                tasks_queued=tasks_queued,
                failure_count=failure_count,
            )
        except Exception as e:
            errors.append("Watchdog error: {}".format(e))

        # Stage 5d: Policy
        try:
            self._policy.evaluate_all(
                has_auto_execution=has_auto_execution,
                has_approval=has_approval,
                pending_approvals=pending_approvals,
                has_conversation=has_conversation,
                is_read_only=is_read_only,
                has_evidence=has_evidence,
                evidence_quality=evidence_quality,
                trust_level=trust_level,
                providers_healthy=provider_healthy,
                providers_total=provider_healthy + provider_degraded,
                missions_active=missions_active,
            )
        except Exception as e:
            errors.append("Policy error: {}".format(e))

        # Stage 5e: Recommendation
        try:
            health = self._health.latest()
            self._recommendation.aggregate(
                health_status=health.status if health else "unknown",
                health_score=health.score.overall_score if health else 1.0,
                health_issues=tuple(health.issues) if health else (),
                policy_violations=tuple(self._policy.violations),
                watchdog_alerts=tuple(self._watchdog.alerts),
                watchdog_warnings=tuple(self._watchdog.warnings),
                watchdog_incidents=tuple(self._watchdog.incidents),
                reasoning_failures=failure_count,
                active_sessions=reasoning_sessions,
            )
        except Exception as e:
            errors.append("Recommendation error: {}".format(e))

        # Stage 6: Conversation
        conv_ok = True
        try:
            self._conversation.get_summary()
        except Exception as e:
            errors.append("Conversation error: {}".format(e))
            conv_ok = False

        # Stage 7: Dashboard
        dash_ok = True
        try:
            self._dashboard.get_dashboard()
        except Exception as e:
            errors.append("Dashboard error: {}".format(e))
            dash_ok = False

        completed = datetime.now().isoformat(timespec="seconds")
        success = len(errors) == 0

        result = SupervisoryPipelineResult(
            pipeline_id=pid,
            observation_ok=observation_ok,
            brain_ok=brain_ok,
            reasoning_ok=reasoning_ok,
            decision_ok=decision_ok,
            supervisor_ok="Supervisor error" not in [e for e in errors],
            conversation_ok=conv_ok,
            dashboard_ok=dash_ok,
            success=success,
            errors=tuple(errors),
            started_at=started,
            completed_at=completed,
        )

        self._results.append(result)
        return result

    @property
    def results(self) -> List[SupervisoryPipelineResult]:
        return list(self._results)

    @property
    def pipeline_count(self) -> int:
        return self._pipeline_count
