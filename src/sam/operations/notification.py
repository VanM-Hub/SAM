"""
NotificationModel — Pure notification framework for operational events.

All notification types are defined as enum-like string constants.
Models only — no desktop notification, no renderer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


# ── Notification types ────────────────────────────────────────────────

MISSION_STARTED = "mission_started"
MISSION_COMPLETED = "mission_completed"
APPROVAL_NEEDED = "approval_needed"
APPROVAL_EXPIRED = "approval_expired"
EXECUTION_FAILED = "execution_failed"
ROLLBACK_EXECUTED = "rollback_executed"
VERIFICATION_FAILED = "verification_failed"
TRUST_DROPPED = "trust_dropped"
RECOVERY_SUCCESS = "recovery_success"
CRITICAL_ALERT = "critical_alert"

NOTIFICATION_TYPES = frozenset({
    MISSION_STARTED,
    MISSION_COMPLETED,
    APPROVAL_NEEDED,
    APPROVAL_EXPIRED,
    EXECUTION_FAILED,
    ROLLBACK_EXECUTED,
    VERIFICATION_FAILED,
    TRUST_DROPPED,
    RECOVERY_SUCCESS,
    CRITICAL_ALERT,
})

# ── Severity mapping ──────────────────────────────────────────────────

NOTIFICATION_SEVERITY = {
    MISSION_STARTED: "information",
    MISSION_COMPLETED: "information",
    APPROVAL_NEEDED: "attention",
    APPROVAL_EXPIRED: "warning",
    EXECUTION_FAILED: "error",
    ROLLBACK_EXECUTED: "warning",
    VERIFICATION_FAILED: "error",
    TRUST_DROPPED: "warning",
    RECOVERY_SUCCESS: "information",
    CRITICAL_ALERT: "critical",
}


# ── Model ─────────────────────────────────────────────────────────────

@dataclass
class Notification:
    """Single operational notification — pure data.

    Fields:
        type_id: One of NOTIFICATION_TYPES constants
        title: Short human-readable title
        message: Detailed message
        source_id: ID of the object that generated this notification
         (mission_id, decision_id, approval_id, etc.)
        source_kind: "mission" | "decision" | "approval" | "execution" | "trust" | "system"
        severity: Computed from type_id
        created_at: ISO timestamp
        acknowledged: Whether user has seen/acknowledged this
    """
    type_id: str
    title: str
    message: str = ""
    source_id: str = ""
    source_kind: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    acknowledged: bool = False

    def __post_init__(self) -> None:
        if self.type_id not in NOTIFICATION_TYPES:
            raise ValueError(f"Unknown notification type: {self.type_id}")

    @property
    def severity(self) -> str:
        return NOTIFICATION_SEVERITY.get(self.type_id, "information")

    @property
    def is_critical(self) -> bool:
        return self.severity == "critical"

    @property
    def is_error(self) -> bool:
        return self.severity == "error"


# ── Factory helpers ───────────────────────────────────────────────────

def notification_mission_started(mission_id: str, mission_name: str) -> Notification:
    return Notification(
        type_id=MISSION_STARTED,
        title=f"Mission started: {mission_name}",
        message=f"Mission {mission_name} ({mission_id}) has started.",
        source_id=mission_id,
        source_kind="mission",
    )


def notification_mission_completed(mission_id: str, mission_name: str,
                                    result: str = "success") -> Notification:
    return Notification(
        type_id=MISSION_COMPLETED,
        title=f"Mission completed: {mission_name}",
        message=f"Mission {mission_name} ({mission_id}) completed with result: {result}.",
        source_id=mission_id,
        source_kind="mission",
    )


def notification_approval_needed(approval_id: str, decision_title: str) -> Notification:
    return Notification(
        type_id=APPROVAL_NEEDED,
        title="Approval needed",
        message=f"Decision '{decision_title}' ({approval_id}) requires your approval.",
        source_id=approval_id,
        source_kind="approval",
    )


def notification_approval_expired(approval_id: str, decision_title: str) -> Notification:
    return Notification(
        type_id=APPROVAL_EXPIRED,
        title="Approval expired",
        message=f"Approval for '{decision_title}' ({approval_id}) has expired.",
        source_id=approval_id,
        source_kind="approval",
    )


def notification_execution_failed(plan_id: str, error: str) -> Notification:
    return Notification(
        type_id=EXECUTION_FAILED,
        title="Execution failed",
        message=f"Execution plan {plan_id} failed: {error}.",
        source_id=plan_id,
        source_kind="execution",
    )


def notification_rollback_executed(plan_id: str, reason: str) -> Notification:
    return Notification(
        type_id=ROLLBACK_EXECUTED,
        title="Rollback executed",
        message=f"Rollback executed for plan {plan_id}: {reason}.",
        source_id=plan_id,
        source_kind="execution",
    )


def notification_verification_failed(plan_id: str, detail: str) -> Notification:
    return Notification(
        type_id=VERIFICATION_FAILED,
        title="Verification failed",
        message=f"Verification failed for plan {plan_id}: {detail}.",
        source_id=plan_id,
        source_kind="execution",
    )


def notification_trust_dropped(mission_id: str, old_score: float,
                                new_score: float) -> Notification:
    return Notification(
        type_id=TRUST_DROPPED,
        title="Trust score dropped",
        message=f"Trust for mission {mission_id} dropped from {old_score:.2f} to {new_score:.2f}.",
        source_id=mission_id,
        source_kind="trust",
    )


def notification_recovery_success(mission_id: str) -> Notification:
    return Notification(
        type_id=RECOVERY_SUCCESS,
        title="Recovery successful",
        message=f"Mission {mission_id} has been successfully recovered.",
        source_id=mission_id,
        source_kind="mission",
    )


def notification_critical_alert(source_id: str, title: str, message: str) -> Notification:
    return Notification(
        type_id=CRITICAL_ALERT,
        title=title,
        message=message,
        source_id=source_id,
        source_kind="system",
    )


# ── Notification Store (in-memory) ────────────────────────────────────

class NotificationStore:
    """Simple in-memory notification storage.

    Not persisted. For production, connect to audit store or dedicated
    notification table.
    """

    def __init__(self, max_size: int = 100) -> None:
        self._notifications: list[Notification] = []
        self._max_size = max_size

    def push(self, notification: Notification) -> None:
        self._notifications.append(notification)
        if len(self._notifications) > self._max_size:
            self._notifications.pop(0)

    def unacknowledged(self) -> list[Notification]:
        return [n for n in self._notifications if not n.acknowledged]

    def all(self) -> list[Notification]:
        return list(self._notifications)

    def acknowledge(self, index: int) -> bool:
        if 0 <= index < len(self._notifications):
            self._notifications[index].acknowledged = True
            return True
        return False

    def acknowledge_all(self) -> int:
        count = 0
        for n in self._notifications:
            if not n.acknowledged:
                n.acknowledged = True
                count += 1
        return count

    def count_unacknowledged(self) -> int:
        return len([n for n in self._notifications if not n.acknowledged])

    def clear(self) -> None:
        self._notifications.clear()
