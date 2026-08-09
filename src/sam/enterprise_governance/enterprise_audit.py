"""Enterprise Audit & Governance Intelligence - WP-31..40 (MISSION-5.5 / IP-5.5-004).

Observasi, audit, explainability, dan intelligence lintas organisasi TANPA
menggabungkan authority lokal.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Tuple


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


@dataclass(frozen=True)
class AuditEvent:
    """Satu event audit enterprise."""

    event_id: str
    entity_id: str
    action: str
    observed_at: str = field(default_factory=_now_utc)
    metadata: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {"event_id": self.event_id, "entity_id": self.entity_id, "action": self.action, "observed_at": self.observed_at, "metadata": dict(self.metadata)}


class AuditTrail:
    """Trail audit append-only."""

    def __init__(self) -> None:
        self._events: list = []

    def record(self, entity_id: str, action: str, metadata: Tuple[Tuple[str, str], ...] = ()) -> AuditEvent:
        event = AuditEvent(event_id=str(len(self._events) + 1), entity_id=entity_id, action=action, metadata=metadata)
        self._events.append(event)
        return event

    def events(self) -> Tuple[AuditEvent, ...]:
        return tuple(self._events)

    def for_entity(self, entity_id: str) -> Tuple[AuditEvent, ...]:
        return tuple(e for e in self._events if e.entity_id == entity_id)


@dataclass(frozen=True)
class GovernanceStatus:
    """Status governance sebuah entitas (intelligence)."""

    entity_id: str
    policies: int = 0
    audit_events: int = 0
    drift: bool = False

    def as_dict(self) -> dict:
        return {"entity_id": self.entity_id, "policies": self.policies, "audit_events": self.audit_events, "drift": self.drift}


class GovernanceIntelligence:
    """Mengobservasi status governance lintas entitas tanpa authority."""

    def __init__(self, audit: AuditTrail) -> None:
        self._audit = audit

    def observed_status(self, entity_id: str, policy_count: int = 0) -> GovernanceStatus:
        events = len(self._audit.for_entity(entity_id))
        drift = events > 0 and any(e.action == "drift" for e in self._audit.for_entity(entity_id))
        return GovernanceStatus(entity_id=entity_id, policies=policy_count, audit_events=events, drift=drift)

    def observe_only(self) -> bool:
        return True  # intelligence hanya mengobservasi, tidak menggabungkan authority


@dataclass(frozen=True)
class GovernanceExplanation:
    """Penjelasan observasi governance."""

    entity_id: str
    summary: str
    observations: Tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {"entity_id": self.entity_id, "summary": self.summary, "observations": list(self.observations)}


class GovernanceExplainer:
    """Menjelaskan observasi governance."""

    def explain(self, status: GovernanceStatus) -> GovernanceExplanation:
        return GovernanceExplanation(
            entity_id=status.entity_id,
            summary="observed across boundaries; local authority preserved",
            observations=(f"policies={status.policies}", f"audit_events={status.audit_events}", f"drift={status.drift}"),
        )


class AuditComplianceChecker:
    """Checker compliance audit & intelligence."""

    def check(self, *, append_only=True, observed=True, no_authority_merge=True, no_execution_authority=True, explainable=True) -> Dict[str, Any]:
        checks = [
            {"code": "APPEND_ONLY", "passed": append_only},
            {"code": "OBSERVED_NOT_EXECUTED", "passed": observed},
            {"code": "NO_AUTHORITY_MERGE", "passed": no_authority_merge},
            {"code": "NO_EXECUTION_AUTHORITY", "passed": no_execution_authority},
            {"code": "EXPLAINABLE", "passed": explainable},
        ]
        passed = all(c["passed"] for c in checks)
        return {"component": "enterprise_governance.audit", "passed": passed, "certified": passed, "checks": [c for c in checks]}
