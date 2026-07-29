"""
OP-334 — Guardian Trend Analyzer

Analisis tren berbasis rule (no AI).
Membaca history/events terakhir dan menghasilkan GuardianTrend.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


# ══════════════════════════════════════════════════════════════════════
# DTOs
# ══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class GuardianTrend:
    """Hasil analisis tren."""
    timestamp: str = ""
    health_trend: str = "stable"
    recommendation_trend: str = "stable"
    watchdog_trend: str = "stable"
    policy_trend: str = "stable"
    anomaly_trend: str = "stable"
    health_count: int = 0
    recommendation_count: int = 0
    watchdog_count: int = 0
    policy_count: int = 0
    anomaly_count: int = 0
    signals: Tuple[str, ...] = field(default_factory=tuple)
    patterns: Tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "health_trend": self.health_trend,
            "recommendation_trend": self.recommendation_trend,
            "watchdog_trend": self.watchdog_trend,
            "policy_trend": self.policy_trend,
            "anomaly_trend": self.anomaly_trend,
            "health_count": self.health_count,
            "recommendation_count": self.recommendation_count,
            "watchdog_count": self.watchdog_count,
            "policy_count": self.policy_count,
            "anomaly_count": self.anomaly_count,
            "signals": list(self.signals),
            "patterns": list(self.patterns),
        }


# ══════════════════════════════════════════════════════════════════════
# Trend Analyzer
# ══════════════════════════════════════════════════════════════════════

class GuardianTrendAnalyzer:
    """Rule-based trend analyzer. Membaca history untuk mendeteksi pola."""

    def __init__(self, history: Any = None):
        self._history = history
        self._trends: List[GuardianTrend] = []

    @property
    def trend_count(self) -> int:
        return len(self._trends)

    @property
    def last_trend(self) -> Optional[GuardianTrend]:
        return self._trends[-1] if self._trends else None

    def analyze(self, **kw: Any) -> GuardianTrend:
        """Analisis tren dari history dan parameter langsung."""
        now = datetime.now().isoformat(timespec="seconds")
        signals: List[str] = []
        patterns: List[str] = []

        # Kumpulkan count dari history
        health_count = 0
        recommendation_count = 0
        watchdog_count = 0
        policy_count = 0
        anomaly_count = 0

        if self._history:
            health_count = len(self._history.by_health())
            watchdog_count = len(self._history.by_watchdog())
            policy_count = len(self._history.by_policy())

        # Parameter langsung override
        health_trend = kw.get("health_trend", self._detect_trend(health_count))
        recommendation_trend = kw.get("recommendation_trend", "stable")
        watchdog_trend = kw.get("watchdog_trend", self._detect_watchdog_trend(kw.get("watchdog_alerts", 0)))
        policy_trend = kw.get("policy_trend", self._detect_trend(policy_count))
        anomaly_trend = kw.get("anomaly_trend", "stable")

        recommendation_count = kw.get("recommendation_count", 0)
        anomaly_count = kw.get("anomaly_count", 0)

        # Signal detection
        self._detect_signals(signals, kw, health_trend, watchdog_trend)

        # Pattern detection
        self._detect_patterns(patterns, kw, health_trend, watchdog_trend)

        trend = GuardianTrend(
            timestamp=now,
            health_trend=health_trend,
            recommendation_trend=self._detect_trend(recommendation_count),
            watchdog_trend=watchdog_trend,
            policy_trend=policy_trend,
            anomaly_trend=anomaly_trend,
            health_count=health_count,
            recommendation_count=recommendation_count,
            watchdog_count=watchdog_count,
            policy_count=policy_count,
            anomaly_count=anomaly_count,
            signals=tuple(signals),
            patterns=tuple(patterns),
        )

        self._trends.append(trend)
        return trend

    # ── Internal ──

    def _detect_trend(self, count: int) -> str:
        if count > 20:
            return "increasing"
        elif count > 10:
            return "slight_increase"
        elif count == 0:
            return "stable"
        return "slight_increase"

    def _detect_watchdog_trend(self, alerts: int) -> str:
        if alerts > 5:
            return "critical"
        elif alerts > 2:
            return "concerning"
        elif alerts > 0:
            return "minor"
        return "stable"

    def _detect_signals(
        self, signals: List[str], kw: Dict[str, Any],
        health_trend: str, watchdog_trend: str,
    ) -> None:
        if health_trend == "degrading":
            signals.append("health_degrading")
        if watchdog_trend in ("concerning", "critical"):
            signals.append("watchdog_active")
        if kw.get("stalled_missions", 0) > 0:
            signals.append("mission_stall_detected")
        if kw.get("retry_count", 0) > 5:
            signals.append("retry_loop_detected")
        if kw.get("queue_depth", 0) > 50:
            signals.append("queue_backlog")
        if kw.get("pending_approvals", 0) > 10:
            signals.append("approval_backlog")

    def _detect_patterns(
        self, patterns: List[str], kw: Dict[str, Any],
        health_trend: str, watchdog_trend: str,
    ) -> None:
        if health_trend == "degrading" and watchdog_trend == "critical":
            patterns.append("system_degradation_with_alerts")
        if kw.get("failure_count", 0) > 5 and kw.get("retry_count", 0) > 3:
            patterns.append("failure_retry_loop")
        if kw.get("provider_healthy", 0) == 0 and kw.get("provider_degraded", 0) > 2:
            patterns.append("provider_degradation")
        if kw.get("pending_approvals", 0) > 10 and kw.get("queue_depth", 0) > 30:
            patterns.append("stall_risk")
