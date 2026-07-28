"""
OP-241 — Observation Engine.

Collects operational signals from all available sources.
Read-only: never modifies state.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ObservationSnapshot:
    """Immutable snapshot of operational state at a point in time."""

    timestamp: float
    active_missions: int
    failed_missions: int
    pending_approvals: int
    locks_held: int
    queue_length: int
    trust_summary: Dict[str, float]
    notification_summary: Dict[str, int]
    telemetry_summary: Dict[str, Any]
    anomalies: List[Dict[str, Any]]

    def __post_init__(self) -> None:
        for k, v in self.__dict__.items():
            if v is None:
                object.__setattr__(self, k, _ZERO_VALUES.get(k, {}))


_ZERO_VALUES = {
    "active_missions": 0,
    "failed_missions": 0,
    "pending_approvals": 0,
    "locks_held": 0,
    "queue_length": 0,
    "trust_summary": {},
    "notification_summary": {},
    "telemetry_summary": {},
    "anomalies": [],
}


class ObservationEngine:
    """Collects read-only operational signals from SAM subsystems.

    Each `collect()` produces a fresh ObservationSnapshot.
    No business logic — pure data gathering.
    """

    def __init__(self) -> None:
        self._last_snapshot: Optional[ObservationSnapshot] = None

    def collect(self) -> ObservationSnapshot:
        """Collect current operational state.

        Falls back gracefully if a source module is unavailable.
        """
        snapshot = ObservationSnapshot(
            timestamp=time.time(),
            active_missions=self._get_active_missions(),
            failed_missions=self._get_failed_missions(),
            pending_approvals=self._get_pending_approvals(),
            locks_held=self._get_locks(),
            queue_length=self._get_queue_length(),
            trust_summary=self._get_trust_summary(),
            notification_summary=self._get_notification_summary(),
            telemetry_summary=self._get_telemetry_summary(),
            anomalies=self._get_anomalies(),
        )
        self._last_snapshot = snapshot
        return snapshot

    @property
    def last_snapshot(self) -> Optional[ObservationSnapshot]:
        return self._last_snapshot

    # ── Private collectors (read-only, graceful fallback) ──────────────

    @staticmethod
    def _get_active_missions() -> int:
        try:
            from sam.operations.mission_query import get_active_missions_count
            return get_active_missions_count()
        except Exception:
            return 0

    @staticmethod
    def _get_failed_missions() -> int:
        try:
            from sam.operations.mission_query import get_failed_missions_count
            return get_failed_missions_count()
        except Exception:
            return 0

    @staticmethod
    def _get_pending_approvals() -> int:
        try:
            from sam.operations.approval import get_pending_count
            return get_pending_count()
        except Exception:
            return 0

    @staticmethod
    def _get_locks() -> int:
        try:
            from sam.operations.workspace_lock import get_active_lock_count
            return get_active_lock_count()
        except Exception:
            return 0

    @staticmethod
    def _get_queue_length() -> int:
        try:
            from sam.operations.providers.queue import QueueProvider
            q = QueueProvider()
            return q.size() if hasattr(q, 'size') else 0
        except Exception:
            return 0

    @staticmethod
    def _get_trust_summary() -> Dict[str, float]:
        try:
            from sam.operations.trust import get_trust_summary
            return get_trust_summary()
        except Exception:
            return {}

    @staticmethod
    def _get_notification_summary() -> Dict[str, int]:
        try:
            from sam.operations.notification import get_notification_summary
            return get_notification_summary()
        except Exception:
            return {"info": 0, "warning": 0, "error": 0, "total": 0}

    @staticmethod
    def _get_telemetry_summary() -> Dict[str, Any]:
        try:
            from sam.telemetry.service import TelemetryService
            svc = TelemetryService()
            return {
                "events_recent": svc.count_recent(seconds=300),
                "rate_per_min": svc.rate_per_minute(),
            }
        except Exception:
            return {"events_recent": 0, "rate_per_min": 0.0}

    @staticmethod
    def _get_anomalies() -> List[Dict[str, Any]]:
        try:
            from sam.intelligence.detector import AnomalyDetector
            det = AnomalyDetector()
            return det.get_recent_anomalies(limit=10)
        except Exception:
            return []


# ── Convenience function ─────────────────────────────────────────────

def collect_observation() -> ObservationSnapshot:
    """One-shot convenience."""
    return ObservationEngine().collect()
