"""
OP-275 — Escalation Planner

Aturan eskalasi untuk approval yang timeout:

  approval timeout → reminder → escalation → critical notification → expired

Tidak mengubah Approval Engine.
Output berupa EscalationPlan DTO.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from datetime import datetime, timedelta


class EscalationLevel(Enum):
    NONE = "none"
    REMINDER = "reminder"
    ESCALATION = "escalation"
    CRITICAL = "critical"
    EXPIRED = "expired"


@dataclass(frozen=True)
class EscalationStep:
    proposal_id: str
    title: str
    level: EscalationLevel
    triggered_at: str
    message: str
    target: str = "approver"  # approver | reviewer | admin
    days_since_creation: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "title": self.title,
            "level": self.level.value,
            "triggered_at": self.triggered_at,
            "message": self.message,
            "target": self.target,
            "days_since_creation": self.days_since_creation,
        }


@dataclass(frozen=True)
class EscalationPlan:
    steps: tuple[EscalationStep, ...]
    total: int = 0
    expired_count: int = 0
    critical_count: int = 0
    escalation_count: int = 0
    reminder_count: int = 0
    generated_at: str = ""

    @property
    def has_active(self) -> bool:
        return any(
            s.level in (EscalationLevel.REMINDER, EscalationLevel.ESCALATION,
                        EscalationLevel.CRITICAL)
            for s in self.steps
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "expired_count": self.expired_count,
            "critical_count": self.critical_count,
            "escalation_count": self.escalation_count,
            "reminder_count": self.reminder_count,
            "generated_at": self.generated_at,
            "steps": [s.to_dict() for s in self.steps],
        }


class EscalationPlanner:
    """
    Merencanakan eskalasi approval timeout.

    Threshold (dalam hari):
      - reminder: 1 hari
      - escalation: 3 hari
      - critical: 7 hari
      - expired: 14 hari
    """

    REMINDER_DAYS: float = 1.0
    ESCALATION_DAYS: float = 3.0
    CRITICAL_DAYS: float = 7.0
    EXPIRED_DAYS: float = 14.0

    def __init__(self,
                 reminder_days: float | None = None,
                 escalation_days: float | None = None,
                 critical_days: float | None = None,
                 expired_days: float | None = None,
                 ) -> None:
        self._reminder = reminder_days or self.REMINDER_DAYS
        self._escalation = escalation_days or self.ESCALATION_DAYS
        self._critical = critical_days or self.CRITICAL_DAYS
        self._expired = expired_days or self.EXPIRED_DAYS

    def plan(self,
             pending_approvals: list[dict[str, Any]],
             now: datetime | None = None,
             ) -> EscalationPlan:
        """
        Generate escalation steps for pending approvals.

        Each pending approval dict may contain:
          - id / proposal_id (required)
          - title (optional)
          - created_at (ISO timestamp, optional)
          - days_pending (float, optional)
        """
        current_time = now or datetime.now()
        now_str = current_time.isoformat(timespec="seconds")

        steps: list[EscalationStep] = []
        expired = 0
        critical = 0
        escalation = 0
        reminder = 0

        for pa in pending_approvals:
            pid = pa.get("id") or pa.get("proposal_id", "?")
            title = str(pa.get("title", pid))
            days = self._get_days(pa, current_time)

            level, message, target = self._evaluate_level(days)

            if level == EscalationLevel.NONE:
                continue

            step = EscalationStep(
                proposal_id=pid,
                title=title,
                level=level,
                triggered_at=now_str,
                message=message,
                target=target,
                days_since_creation=round(days, 1),
            )
            steps.append(step)

            if level == EscalationLevel.REMINDER:
                reminder += 1
            elif level == EscalationLevel.ESCALATION:
                escalation += 1
            elif level == EscalationLevel.CRITICAL:
                critical += 1
            elif level == EscalationLevel.EXPIRED:
                expired += 1

        return EscalationPlan(
            steps=tuple(steps),
            total=len(steps),
            expired_count=expired,
            critical_count=critical,
            escalation_count=escalation,
            reminder_count=reminder,
            generated_at=now_str,
        )

    def _get_days(self, item: dict[str, Any], now: datetime) -> float:
        if "days_pending" in item:
            return float(item["days_pending"])

        created_str = item.get("created_at")
        if created_str:
            try:
                created = datetime.fromisoformat(created_str)
                return (now - created).total_seconds() / 86400.0
            except (ValueError, TypeError):
                pass
        return 0.0

    def _evaluate_level(self, days: float) -> tuple[EscalationLevel, str, str]:
        if days >= self._expired:
            return (
                EscalationLevel.EXPIRED,
                f"Proposal telah expired setelah {days:.0f} hari tanpa approval",
                "admin",
            )
        if days >= self._critical:
            return (
                EscalationLevel.CRITICAL,
                f"Approval critical — {days:.0f} hari menunggu, segera ditindaklanjuti",
                "approver",
            )
        if days >= self._escalation:
            return (
                EscalationLevel.ESCALATION,
                f"Approval perlu eskalasi — {days:.0f} hari menunggu",
                "reviewer",
            )
        if days >= self._reminder:
            return (
                EscalationLevel.REMINDER,
                f"Reminder: approval menunggu selama {days:.0f} hari",
                "approver",
            )
        return (EscalationLevel.NONE, "", "")
