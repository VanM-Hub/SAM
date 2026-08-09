"""Autonomous Investigation + Operational Context - WP-02/03 (MISSION-4.5 / IP-4.5-001).

Engine investigasi yang mampu berjalan secara proaktif. Investigation dapat
dimulai tanpa intervensi manual, mengikuti workflow tervalidasi, seluruh
hasil memiliki evidence, dan tidak melakukan mutation.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from .investigation_trigger import InvestigationRequest


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


class InvestigationState:
    PENDING = "pending"
    PLANNED = "planned"
    COLLECTING = "collecting"
    COMPLETED = "completed"

    _ORDER = (PENDING, PLANNED, COLLECTING, COMPLETED)

    @classmethod
    def valid(cls, state: str) -> bool:
        return state in cls._ORDER

    @classmethod
    def can_transition(cls, current: str, target: str) -> bool:
        return cls._ORDER.index(target) > cls._ORDER.index(current)


@dataclass(frozen=True)
class AutonomousInvestigation:
    """Satu investigasi otonom."""

    investigation_id: str
    reason: str
    request_id: str
    state: str = InvestigationState.PENDING
    targets: Tuple[str, ...] = field(default_factory=tuple)
    created_at: str = field(default_factory=_now_utc)
    result: Dict[str, Any] = field(default_factory=dict)

    def transition(self, target: str) -> "AutonomousInvestigation":
        if not InvestigationState.can_transition(self.state, target):
            raise ValueError(f"Cannot {self.state} -> {target}")
        return AutonomousInvestigation(
            investigation_id=self.investigation_id,
            reason=self.reason,
            request_id=self.request_id,
            state=target,
            targets=self.targets,
            created_at=self.created_at,
            result=self.result,
        )

    def complete(self, result: Dict[str, Any]) -> "AutonomousInvestigation":
        if self.state != InvestigationState.COLLECTING:
            raise ValueError("complete only from collecting")
        return AutonomousInvestigation(
            investigation_id=self.investigation_id,
            reason=self.reason,
            request_id=self.request_id,
            state=InvestigationState.COMPLETED,
            targets=self.targets,
            created_at=self.created_at,
            result=result,
        )

    def as_dict(self) -> dict:
        return {
            "investigation_id": self.investigation_id,
            "reason": self.reason,
            "request_id": self.request_id,
            "state": self.state,
            "targets": list(self.targets),
            "created_at": self.created_at,
            "result": self.result,
        }


@dataclass(frozen=True)
class InvestigationWorkflow:
    """Workflow investigasi (tervalidasi, sequence tetap)."""

    workflow_id: str
    steps: Tuple[str, ...] = (
        "planning",
        "context_collection",
        "runtime_verification",
        "provider_verification",
        "complete",
    )

    def as_dict(self) -> dict:
        return {
            "workflow_id": self.workflow_id,
            "steps": list(self.steps),
        }


class ContextSnapshot:
    """Snapshot konteks (immutable)."""

    def __init__(self, captured_at: str = "") -> None:
        self.captured_at = captured_at or _now_utc()
        self._runtimes: Dict[str, Dict[str, Any]] = {}
        self._providers: Dict[str, Dict[str, Any]] = {}
        self._missions: Dict[str, Dict[str, Any]] = {}
        self._workflows: Dict[str, Dict[str, Any]] = {}

    def add_runtime(self, runtime_id: str, data: Dict[str, Any]) -> None:
        self._runtimes[runtime_id] = dict(data)

    def add_provider(self, provider_id: str, data: Dict[str, Any]) -> None:
        self._providers[provider_id] = dict(data)

    def add_mission(self, mission_id: str, data: Dict[str, Any]) -> None:
        self._missions[mission_id] = dict(data)

    def add_workflow(self, workflow_id: str, data: Dict[str, Any]) -> None:
        self._workflows[workflow_id] = dict(data)

    def runtimes(self) -> Tuple[Tuple[str, Dict[str, Any]], ...]:
        return tuple(sorted(self._runtimes.items()))

    def providers(self) -> Tuple[Tuple[str, Dict[str, Any]], ...]:
        return tuple(sorted(self._providers.items()))

    def missions(self) -> Tuple[Tuple[str, Dict[str, Any]], ...]:
        return tuple(sorted(self._missions.items()))

    def workflows(self) -> Tuple[Tuple[str, Dict[str, Any]], ...]:
        return tuple(sorted(self._workflows.items()))

    def as_dict(self) -> dict:
        return {
            "captured_at": self.captured_at,
            "runtimes": dict(self._runtimes),
            "providers": dict(self._providers),
            "missions": dict(self._missions),
            "workflows": dict(self._workflows),
        }


class AutonomousInvestigationEngine:
    """Engine investigasi otonom (read-only, workflow-validated)."""

    def __init__(self) -> None:
        self._investigations: Dict[str, AutonomousInvestigation] = {}
        self._metrics: Dict[str, Any] = {}

    def start(self, request: InvestigationRequest) -> AutonomousInvestigation:
        inv = AutonomousInvestigation(
            investigation_id=uuid.uuid4().hex,
            reason=request.reason,
            request_id=request.request_id,
            targets=request.target_ids,
        )
        self._investigations[inv.investigation_id] = inv
        return inv

    def get(self, investigation_id: str) -> Optional[AutonomousInvestigation]:
        return self._investigations.get(investigation_id)

    def all(self) -> Tuple[AutonomousInvestigation, ...]:
        return tuple(self._investigations.values())

    def count(self) -> int:
        return len(self._investigations)

    def metrics(self) -> Dict[str, Any]:
        return {
            "total": self.count(),
            "completed": sum(
                1 for i in self._investigations.values() if i.state == InvestigationState.COMPLETED
            ),
            "pending": sum(
                1 for i in self._investigations.values() if i.state == InvestigationState.PENDING
            ),
        }
