"""
OP-323 — Guardian Watchdog

Deteksi:
  - stuck reasoning
  - provider timeout
  - approval deadlock
  - queue starvation
  - mission stall
  - retry loop
  - scheduler overload
  - repeated failures

Output: GuardianAlert, GuardianWarning, GuardianIncident
Tidak memperbaiki apapun — hanya mendeteksi.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


@dataclass(frozen=True)
class GuardianAlert:
    alert_type: str
    severity: str  # info, warning, critical
    component: str
    message: str
    detail: str = ""
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_type": self.alert_type,
            "severity": self.severity,
            "component": self.component,
            "message": self.message,
            "detail": self.detail,
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class GuardianWarning:
    warning_type: str
    component: str
    message: str
    detail: str = ""
    recommendation: str = ""
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "warning_type": self.warning_type,
            "component": self.component,
            "message": self.message,
            "detail": self.detail,
            "recommendation": self.recommendation,
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class GuardianIncident:
    incident_type: str
    severity: str  # medium, high, critical
    component: str
    message: str
    detail: str = ""
    occurrence_count: int = 1
    first_seen: str = ""
    last_seen: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "incident_type": self.incident_type,
            "severity": self.severity,
            "component": self.component,
            "message": self.message,
            "detail": self.detail,
            "occurrence_count": self.occurrence_count,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
        }


class GuardianWatchdog:
    """
    Watchdog — hanya deteksi, tidak memperbaiki.
    """

    def __init__(self) -> None:
        self._alerts: List[GuardianAlert] = []
        self._warnings: List[GuardianWarning] = []
        self._incidents: Dict[str, GuardianIncident] = {}
        self._max_records: int = 100

    def check_stuck_reasoning(
        self,
        reasoning_sessions: int = 0,
        reasoning_max_duration_ms: float = 0.0,
        threshold_ms: float = 60000.0,
    ) -> Optional[GuardianAlert]:
        if reasoning_sessions > 0 and reasoning_max_duration_ms > threshold_ms:
            alert = GuardianAlert(
                alert_type="stuck_reasoning",
                severity="critical",
                component="reasoning",
                message="Reasoning session exceeded max duration",
                detail="{:.0f}ms (threshold {:.0f}ms)".format(
                    reasoning_max_duration_ms, threshold_ms
                ),
                timestamp=datetime.now().isoformat(timespec="seconds"),
            )
            self._alerts.append(alert)
            self._trim()
            return alert
        return None

    def check_provider_timeout(
        self,
        provider_errors: int = 0,
        error_threshold: int = 3,
    ) -> Optional[GuardianWarning]:
        if provider_errors > error_threshold:
            warn = GuardianWarning(
                warning_type="provider_timeout",
                component="provider",
                message="Provider timeout detected",
                detail="{} consecutive errors".format(provider_errors),
                recommendation="Rotate provider or retry later",
                timestamp=datetime.now().isoformat(timespec="seconds"),
            )
            self._warnings.append(warn)
            self._trim()
            return warn
        return None

    def check_approval_deadlock(
        self,
        pending_approvals: int = 0,
        stale_hours: float = 0.0,
        stale_threshold: float = 24.0,
    ) -> Optional[GuardianAlert]:
        if pending_approvals > 0 and stale_hours > stale_threshold:
            alert = GuardianAlert(
                alert_type="approval_deadlock",
                severity="critical",
                component="approval",
                message="Approval deadlock detected",
                detail="{} pending, {:.1f}h stale".format(pending_approvals, stale_hours),
                timestamp=datetime.now().isoformat(timespec="seconds"),
            )
            self._alerts.append(alert)
            self._trim()
            return alert
        return None

    def check_queue_starvation(
        self,
        queue_depth: int = 0,
        queue_processed: int = 0,
        starve_threshold: int = 50,
    ) -> Optional[GuardianWarning]:
        if queue_depth > starve_threshold and queue_processed == 0:
            warn = GuardianWarning(
                warning_type="queue_starvation",
                component="queue",
                message="Queue starvation — no items processed",
                detail="{} queued, 0 processed".format(queue_depth),
                recommendation="Investigate queue consumer",
                timestamp=datetime.now().isoformat(timespec="seconds"),
            )
            self._warnings.append(warn)
            self._trim()
            return warn
        return None

    def check_mission_stall(
        self,
        stalled_missions: int = 0,
        active_missions: int = 0,
    ) -> Optional[GuardianAlert]:
        if stalled_missions > 0 and active_missions > 0:
            ratio = stalled_missions / max(active_missions, 1)
            if ratio > 0.5:
                alert = GuardianAlert(
                    alert_type="mission_stall",
                    severity="critical",
                    component="mission",
                    message="More than half missions stalled",
                    detail="{}/{} stalled".format(stalled_missions, active_missions),
                    timestamp=datetime.now().isoformat(timespec="seconds"),
                )
                self._alerts.append(alert)
                self._trim()
                return alert
        return None

    def check_retry_loop(
        self,
        retry_count: int = 0,
        retry_threshold: int = 5,
    ) -> Optional[GuardianWarning]:
        if retry_count > retry_threshold:
            warn = GuardianWarning(
                warning_type="retry_loop",
                component="execution",
                message="Excessive retry loop detected",
                detail="{} retries (threshold {})".format(retry_count, retry_threshold),
                recommendation="Checkpoint mission before retry",
                timestamp=datetime.now().isoformat(timespec="seconds"),
            )
            self._warnings.append(warn)
            self._trim()
            return warn
        return None

    def check_scheduler_overload(
        self,
        tasks_queued: int = 0,
        scheduler_capacity: int = 100,
    ) -> Optional[GuardianAlert]:
        if tasks_queued > scheduler_capacity:
            alert = GuardianAlert(
                alert_type="scheduler_overload",
                severity="critical",
                component="scheduler",
                message="Scheduler overloaded",
                detail="{} queued (capacity {})".format(tasks_queued, scheduler_capacity),
                timestamp=datetime.now().isoformat(timespec="seconds"),
            )
            self._alerts.append(alert)
            self._trim()
            return alert
        return None

    def check_repeated_failures(
        self,
        failure_count: int = 0,
        failure_threshold: int = 10,
    ) -> Optional[GuardianIncident]:
        if failure_count >= failure_threshold:
            key = "repeated_failures"
            now = datetime.now().isoformat(timespec="seconds")
            if key in self._incidents:
                old = self._incidents[key]
                self._incidents[key] = GuardianIncident(
                    incident_type=key,
                    severity="high",
                    component="system",
                    message="Repeated failures detected",
                    detail="{} total failures".format(failure_count),
                    occurrence_count=old.occurrence_count + 1,
                    first_seen=old.first_seen,
                    last_seen=now,
                )
            else:
                self._incidents[key] = GuardianIncident(
                    incident_type=key,
                    severity="high",
                    component="system",
                    message="Repeated failures detected",
                    detail="{} total failures".format(failure_count),
                    occurrence_count=1,
                    first_seen=now,
                    last_seen=now,
                )
            self._trim()
            return self._incidents[key]
        return None

    def run_all(
        self,
        reasoning_sessions: int = 0,
        reasoning_max_duration_ms: float = 0.0,
        provider_errors: int = 0,
        pending_approvals: int = 0,
        stale_hours: float = 0.0,
        queue_depth: int = 0,
        queue_processed: int = 0,
        stalled_missions: int = 0,
        active_missions: int = 0,
        retry_count: int = 0,
        tasks_queued: int = 0,
        failure_count: int = 0,
        scheduler_capacity: int = 100,
        reasoning_threshold_ms: float = 60000.0,
        provider_error_threshold: int = 3,
        approval_stale_threshold: float = 24.0,
        queue_starve_threshold: int = 50,
        retry_threshold: int = 5,
        failure_threshold: int = 10,
    ) -> Dict[str, Any]:
        return {
            "alerts": self.check_stuck_reasoning(reasoning_sessions, reasoning_max_duration_ms, reasoning_threshold_ms),
            "warnings": [
                self.check_provider_timeout(provider_errors, provider_error_threshold),
                self.check_queue_starvation(queue_depth, queue_processed, queue_starve_threshold),
                self.check_retry_loop(retry_count, retry_threshold),
            ],
            "alerts": [
                self.check_approval_deadlock(pending_approvals, stale_hours, approval_stale_threshold),
                self.check_mission_stall(stalled_missions, active_missions),
                self.check_scheduler_overload(tasks_queued, scheduler_capacity),
            ],
            "incidents": [
                self.check_repeated_failures(failure_count, failure_threshold),
            ],
        }

    @property
    def alerts(self) -> List[GuardianAlert]:
        return list(self._alerts)

    @property
    def warnings(self) -> List[GuardianWarning]:
        return list(self._warnings)

    @property
    def incidents(self) -> List[GuardianIncident]:
        return list(self._incidents.values())

    def clear(self) -> None:
        self._alerts.clear()
        self._warnings.clear()
        self._incidents.clear()

    def _trim(self) -> None:
        if len(self._alerts) > self._max_records:
            self._alerts = self._alerts[-self._max_records:]
        if len(self._warnings) > self._max_records:
            self._warnings = self._warnings[-self._max_records:]
