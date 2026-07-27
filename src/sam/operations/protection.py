"""
Protection Cycle — Autorecovery + Protection Rules.

Bukan Guardian. Protection = sistem yang melindungi diri sendiri.
Cycle berjalan periodik, baca telemetry, terapkan rules.

Alur:
1. Check health signals (CPU, memory, error rate, cras loop)
2. Evaluate rules (threshold-based)
3. Auto-recovery jika memungkinkan
4. Rekomendasi ke manusia jika tidak
5. Kirim event ke Telemetry Service
"""

import structlog
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional

logger = structlog.get_logger()


# ============================================================================
# Models
# ============================================================================

class ProtectionLevel(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    PROBLEM = "problem"
    CRITICAL = "critical"


class RecoveryAction(Enum):
    RESTART_COMPONENT = "restart_component"
    CLEAR_CACHE = "clear_cache"
    RETRY_FAILED = "retry_failed"
    REDUCE_RATE = "reduce_rate"
    NOTIFY_HUMAN = "notify_human"
    WAIT = "wait"


@dataclass
class HealthSignal:
    component: str
    level: ProtectionLevel
    message: str
    value: float = 0.0
    threshold: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class RecoveryAttempt:
    action: RecoveryAction
    component: str
    reason: str
    success: Optional[bool] = None
    result: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ProtectionReport:
    cycle_id: str
    timestamp: str
    level: ProtectionLevel
    signals: List[HealthSignal] = field(default_factory=list)
    recoveries: List[RecoveryAttempt] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    summary: str = "All systems healthy."


# ============================================================================
# Protection Engine
# ============================================================================

class ProtectionEngine:
    """Engine yang menjalankan protection cycle periodik."""

    def __init__(self):
        self._cycle_count = 0
        self._last_report: Optional[ProtectionReport] = None
        self._cooldowns: dict = {}  # component -> next check time

    async def run_cycle(self, telemetry=None) -> ProtectionReport:
        """Jalankan satu protection cycle."""
        self._cycle_count += 1
        now = datetime.now()
        signals: List[HealthSignal] = []
        recoveries: List[RecoveryAttempt] = []

        # 1. Check health signals
        signals = self._check_signals(telemetry)

        # 2. Tentukan level
        level = ProtectionLevel.HEALTHY
        for s in signals:
            order = {
                ProtectionLevel.HEALTHY: 0,
                ProtectionLevel.WARNING: 1,
                ProtectionLevel.PROBLEM: 2,
                ProtectionLevel.CRITICAL: 3,
            }
            if order.get(s.level, 0) > order.get(level, 0):
                level = s.level

        # 3. Auto-recovery untuk PROBLEM/CRITICAL
        if level in (ProtectionLevel.PROBLEM, ProtectionLevel.CRITICAL):
            recoveries = self._try_recovery(signals)

        # 4. Rekomendasi
        recommendations = self._generate_recommendations(level, signals, recoveries)

        # 5. Summary
        summary = self._summarize(level, signals, recoveries)

        report = ProtectionReport(
            cycle_id=f"PC-{self._cycle_count:04d}",
            timestamp=now.isoformat(),
            level=level,
            signals=signals,
            recoveries=recoveries,
            recommendations=recommendations,
            summary=summary,
        )

        # Kirim event ke telemetry
        if telemetry:
            telemetry.emit("protection.cycle.complete", {
                "level": level.value,
                "signals": len(signals),
                "recoveries": len(recoveries),
            })

        self._last_report = report
        logger.info("protection.cycle", cycle=report.cycle_id, level=level.value)

        return report

    def get_last_report(self) -> Optional[ProtectionReport]:
        return self._last_report

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _check_signals(self, telemetry=None) -> List[HealthSignal]:
        """Kumpulkan health signals dari berbagai sumber."""
        signals: List[HealthSignal] = []

        if telemetry:
            # Dari ring buffer — error rate
            events = telemetry.ring_buffer.get_recent(100)
            error_count = sum(1 for e in events if getattr(e, "error", False))
            total = len(events)
            error_rate = error_count / max(total, 1)

            if error_rate > 0.5:
                signals.append(HealthSignal(
                    component="system",
                    level=ProtectionLevel.CRITICAL,
                    message="Error rate above 50%",
                    value=error_rate,
                    threshold=0.5,
                ))
            elif error_rate > 0.2:
                signals.append(HealthSignal(
                    component="system",
                    level=ProtectionLevel.PROBLEM,
                    message="Error rate above 20%",
                    value=error_rate,
                    threshold=0.2,
                ))
            elif error_rate > 0.05:
                signals.append(HealthSignal(
                    component="system",
                    level=ProtectionLevel.WARNING,
                    message="Elevated error rate",
                    value=error_rate,
                    threshold=0.05,
                ))
            else:
                signals.append(HealthSignal(
                    component="system",
                    level=ProtectionLevel.HEALTHY,
                    message="Error rate normal",
                    value=error_rate,
                    threshold=0.05,
                ))

            # Crash loop detection
            crash_signals = [e for e in events if getattr(e, "type", "") == "crash"]
            if len(crash_signals) > 10:
                signals.append(HealthSignal(
                    component="crash_detector",
                    level=ProtectionLevel.CRITICAL,
                    message="Crash loop detected: {} crashes".format(len(crash_signals)),
                    value=float(len(crash_signals)),
                    threshold=10,
                ))
        else:
            # Tanpa telemetry — sinyal default
            signals.append(HealthSignal(
                component="system",
                level=ProtectionLevel.HEALTHY,
                message="No telemetry data — no issues detected",
            ))

        return signals

    def _try_recovery(self, signals: List[HealthSignal]) -> List[RecoveryAttempt]:
        """Coba recovery otomatis."""
        recoveries = []

        for s in signals:
            if s.level == ProtectionLevel.CRITICAL and s.component == "crash_detector":
                recoveries.append(RecoveryAttempt(
                    action=RecoveryAction.NOTIFY_HUMAN,
                    component="crash_detector",
                    reason="Crash loop detected — human intervention required",
                    success=None,
                ))

            if s.component == "system" and s.level in (ProtectionLevel.PROBLEM, ProtectionLevel.CRITICAL):
                recoveries.append(RecoveryAttempt(
                    action=RecoveryAction.NOTIFY_HUMAN,
                    component="system",
                    reason="Error rate above threshold — review required",
                    success=None,
                ))

        return recoveries

    def _generate_recommendations(
        self,
        level: ProtectionLevel,
        signals: List[HealthSignal],
        recoveries: List[RecoveryAttempt],
    ) -> List[str]:
        recs = []

        if level == ProtectionLevel.HEALTHY:
            recs.append("No action needed.")
        elif level == ProtectionLevel.WARNING:
            recs.append("Monitor the situation. No immediate action.")
        elif level == ProtectionLevel.PROBLEM:
            recs.append("Review recent activity and check for errors.")
        elif level == ProtectionLevel.CRITICAL:
            recs.append("Immediate review required.")
            for s in signals:
                if s.level == ProtectionLevel.CRITICAL:
                    recs.append("  - {}: {}".format(s.component, s.message))

        return recs

    def _summarize(
        self,
        level: ProtectionLevel,
        signals: List[HealthSignal],
        recoveries: List[RecoveryAttempt],
    ) -> str:
        if level == ProtectionLevel.HEALTHY:
            return "All systems healthy."
        if level == ProtectionLevel.WARNING:
            return "Minor issues detected, no action needed."
        if level == ProtectionLevel.PROBLEM:
            num = len([s for s in signals if s.level.value in ("problem", "critical")])
            return "{} issue{} detected. Review recommended.".format(
                num, "s" if num > 1 else ""
            )
        return "Critical issues detected. Immediate attention required."


# ============================================================================
# Scheduler
# ============================================================================

class ProtectionScheduler:
    """Periodic protection cycle scheduler.

    Bisa dijalankan sebagai asyncio task di background.
    """

    def __init__(self, engine: ProtectionEngine, interval: float = 30.0):
        self.engine = engine
        self.interval = interval
        self._running = False

    async def start(self, telemetry=None):
        self._running = True
        logger.info(
            "protection.scheduler.started",
            interval=self.interval,
        )
        while self._running:
            await self.engine.run_cycle(telemetry)
            await asyncio.sleep(self.interval)

    async def stop(self):
        self._running = False
        logger.info("protection.scheduler.stopped")
