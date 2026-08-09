"""Investigation Trigger - WP-01 (MISSION-4.5 / IP-4.5-001).

Mekanisme pemicu investigasi berdasarkan kondisi operasional. Trigger
dievaluasi secara deterministik, menghasilkan Investigation Request, memiliki
evidence, dan dapat diaudit.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, List, Optional, Tuple


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


@dataclass(frozen=True)
class TriggerPolicy:
    """Kebijakan pemicu (rule kondisi operasional)."""

    policy_id: str
    condition: str  # misal "health == critical"
    threshold: Any = None
    severity: str = "warning"  # info | warning | critical
    enabled: bool = True

    def as_dict(self) -> dict:
        return {
            "policy_id": self.policy_id,
            "condition": self.condition,
            "threshold": self.threshold,
            "severity": self.severity,
            "enabled": self.enabled,
        }


@dataclass(frozen=True)
class TriggerEvent:
    """Satu event pemicu (evidence)."""

    event_id: str
    policy_id: str
    target_id: str
    condition_matched: str
    observed_value: Any
    severity: str = "warning"
    at: str = field(default_factory=_now_utc)

    def as_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "policy_id": self.policy_id,
            "target_id": self.target_id,
            "condition_matched": self.condition_matched,
            "observed_value": self.observed_value,
            "severity": self.severity,
            "at": self.at,
        }


@dataclass(frozen=True)
class InvestigationRequest:
    """Request investigasi yang dihasilkan trigger."""

    request_id: str
    reason: str
    target_ids: Tuple[str, ...] = field(default_factory=tuple)
    severity: str = "warning"
    source_event_id: str = ""
    created_at: str = field(default_factory=_now_utc)

    def as_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "reason": self.reason,
            "target_ids": list(self.target_ids),
            "severity": self.severity,
            "source_event_id": self.source_event_id,
            "created_at": self.created_at,
        }


class TriggerEvaluationEngine:
    """Mesin evaluasi trigger (deterministik, rule-based)."""

    def __init__(self) -> None:
        self._audit: List[TriggerEvent] = []

    def evaluate(
        self,
        policy: TriggerPolicy,
        *,
        target_id: str,
        observed_value: Any,
    ) -> Optional[TriggerEvent]:
        if not policy.enabled:
            return None
        matched = self._match(policy.condition, observed_value, policy.threshold)
        if not matched:
            return None
        event = TriggerEvent(
            event_id=uuid.uuid4().hex,
            policy_id=policy.policy_id,
            target_id=target_id,
            condition_matched=policy.condition,
            observed_value=observed_value,
            severity=policy.severity,
        )
        self._audit.append(event)
        return event

    @staticmethod
    def _match(condition: str, value: Any, threshold: Any) -> bool:
        text = condition.lower()
        try:
            if "critical" in text:
                return str(value).lower() in ("critical", "error", "failed")
            if "degraded" in text:
                return str(value).lower() in ("degraded", "warning")
            if ">=" in text:
                return float(value) >= float(threshold)
            if ">" in text:
                return float(value) > float(threshold)
            if "<=" in text:
                return float(value) <= float(threshold)
            if "<" in text:
                return float(value) < float(threshold)
            if "==" in text or "=" in text:
                return str(value) == str(threshold)
            if "high" in text:
                return str(value).lower() == "high"
        except (ValueError, TypeError):
            return False
        return False

    def audit(self) -> Tuple[TriggerEvent, ...]:
        return tuple(self._audit)

    def create_request(self, event: TriggerEvent, reason: str) -> InvestigationRequest:
        return InvestigationRequest(
            request_id=uuid.uuid4().hex,
            reason=reason,
            target_ids=(event.target_id,),
            severity=event.severity,
            source_event_id=event.event_id,
        )
