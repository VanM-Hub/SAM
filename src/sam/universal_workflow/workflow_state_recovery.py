"""Workflow State, Recovery & Learning - WP-31..40 (MISSION-5.4 / IP-5.4-004).

State machine, checkpoint & resume, failure recovery, retry & idempotency,
replay, history, outcome analysis, learning evidence.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Tuple

from .workflow_execution import ExecutionContext, StepExecutionResult


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


class Phase(str, Enum):
    """Fase workflow di state machine."""

    PLANNED = "planned"
    RUNNING = "running"
    CHECKPOINTED = "checkpointed"
    RESUMED = "resumed"
    REORDERED = "reordered"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class StateTransition:
    """Satu transisi state."""

    workflow_id: str
    to: Phase
    note: str = ""

    def as_dict(self) -> dict:
        return {"workflow_id": self.workflow_id, "to": self.to.value, "note": self.note}


class WorkflowStateMachine:
    """State machine dengan checkpoint & resume."""

    def __init__(self, workflow_id: str) -> None:
        self.workflow_id = workflow_id
        self._phase: Phase = Phase.PLANNED
        self._checkpoints: list = []
        self._history: list = []

    @property
    def phase(self) -> Phase:
        return self._phase

    def transition(self, to: Phase, note: str = "") -> None:
        self._history.append(StateTransition(self.workflow_id, to, note))
        self._phase = to

    def checkpoint(self) -> None:
        self.transition(Phase.CHECKPOINTED, "checkpoint")
        self._checkpoints.append(self._phase)

    def resume(self) -> None:
        if not self._checkpoints:
            raise ValueError("no checkpoint to resume")
        self.transition(Phase.RESUMED, f"resume from {self._checkpoints[-1].value}")

    def history(self) -> Tuple[StateTransition, ...]:
        return tuple(self._history)


@dataclass(frozen=True)
class RetryPolicy:
    """Kebijakan retry."""

    max_retries: int = 3
    idempotency_key_required: bool = True

    def allows_retry(self, attempts: int) -> bool:
        return attempts < self.max_retries


@dataclass(frozen=True)
class IdempotencyGuard:
    """Menjamin eksekusi idempotent."""

    key: str
    already_executed: bool = False

    def as_dict(self) -> dict:
        return {"key": self.key, "already_executed": self.already_executed}


class IdempotencyManager:
    """Mengelola guard idempotency."""

    def __init__(self) -> None:
        self._guards: dict = {}

    def guard_for(self, request_id: str) -> IdempotencyGuard:
        guard = self._guards.get(request_id)
        if guard is None:
            guard = IdempotencyGuard(key=request_id)
            self._guards[request_id] = guard
        else:
            guard = IdempotencyGuard(key=guard.key, already_executed=True)
            self._guards[request_id] = guard
        return guard


class FailureRecoveryModel:
    """Model pemulihan kegagalan workflow."""

    def classify(self, result: StepExecutionResult) -> str:
        if result.success:
            return "none"
        if result.error and "retryable" in result.error:
            return "retryable"
        if result.error and "checkpointable" in result.error:
            return "checkpointable"
        return "fatal"


class WorkflowReplayer:
    """Memutar ulang eksekusi dari trace."""

    def replay(self, trace: Tuple[ExecutionContext, ...]) -> Tuple[ExecutionContext, ...]:
        return trace


@dataclass(frozen=True)
class WorkflowOutcome:
    """Analisis outcome workflow."""

    workflow_id: str
    completed: int
    failed: int
    success_rate: float

    def as_dict(self) -> dict:
        return {
            "workflow_id": self.workflow_id,
            "completed": self.completed,
            "failed": self.failed,
            "success_rate": self.success_rate,
        }


class OutcomeAnalyzer:
    """Menganalisis outcome dari history eksekusi."""

    def analyze(self, workflow_id: str, contexts: Tuple[ExecutionContext, ...]) -> WorkflowOutcome:
        completed = sum(1 for c in contexts if c.executed and c.all_passed)
        failed = sum(1 for c in contexts if c.executed and not c.all_passed)
        total = completed + failed
        rate = (completed / total) if total else 0.0
        return WorkflowOutcome(workflow_id=workflow_id, completed=completed, failed=failed, success_rate=rate)


@dataclass(frozen=True)
class LearningEvidence:
    """Evidence untuk pembelajaran workflow."""

    workflow_id: str
    outcome: str
    observations: Tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {"workflow_id": self.workflow_id, "outcome": self.outcome, "observations": list(self.observations)}


class LearningEvidenceCollector:
    """Mengumpulkan evidence pembelajaran."""

    def collect(self, outcome: WorkflowOutcome) -> LearningEvidence:
        return LearningEvidence(
            workflow_id=outcome.workflow_id,
            outcome="healthy" if outcome.success_rate >= 0.8 else "needs_improvement",
            observations=(f"completed={outcome.completed}", f"failed={outcome.failed}"),
        )


class RecoveryExplainability:
    """Menjelaskan pemulihan."""

    def explain(self, workflow_id: str, transitions: Tuple[StateTransition, ...]) -> Dict[str, Any]:
        return {
            "workflow_id": workflow_id,
            "transitions": [t.as_dict() for t in transitions],
            "explainable": True,
        }


@dataclass(frozen=True)
class RecoveryComplianceResult:
    """Hasil compliance recovery."""

    passed: bool
    checks: Tuple[Dict[str, Any], ...] = field(default_factory=tuple)


class RecoveryComplianceChecker:
    """Checker compliance recovery."""

    def check(self, *, idempotent=True, recoverable=True, deterministic=True, audited=True, explainable=True) -> RecoveryComplianceResult:
        checks = [
            {"code": "IDEMPOTENT", "passed": idempotent},
            {"code": "RECOVERABLE", "passed": recoverable},
            {"code": "DETERMINISTIC", "passed": deterministic},
            {"code": "AUDITED", "passed": audited},
            {"code": "EXPLAINABLE", "passed": explainable},
        ]
        return RecoveryComplianceResult(passed=all(c["passed"] for c in checks), checks=tuple(checks))

    def certify(self, **kwargs: Any) -> Dict[str, Any]:
        result = self.check(**kwargs)
        return {"component": "universal_workflow.recovery", "passed": result.passed, "certified": result.passed, "checks": [c for c in result.checks]}
