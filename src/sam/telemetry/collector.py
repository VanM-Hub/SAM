"""
Metrics Collector — Phase 1

Mengumpulkan CPU, memory, uptime secara periodik.
Terintegrasi dengan Runtime Coordinator dan TelemetryService.
"""

import asyncio
import structlog
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

logger = structlog.get_logger()


@dataclass
class RuntimeMetrics:
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    uptime_seconds: float = 0.0
    active_sessions: int = 0
    event_count: int = 0
    last_error: Optional[str] = None


class MetricsCollector:
    def __init__(self, interval: float = 5.0):
        self.interval = interval
        self._running = False
        self._metrics = RuntimeMetrics()

    async def start(self):
        self._running = True
        logger.info("metrics.collector.started", interval=self.interval)
        while self._running:
            await self._collect()
            await asyncio.sleep(self.interval)

    async def stop(self):
        self._running = False
        logger.info("metrics.collector.stopped")

    async def _collect(self):
        import psutil

        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory().percent
        uptime = self._read_uptime()

        self._metrics = RuntimeMetrics(
            cpu_percent=cpu,
            memory_percent=mem,
            uptime_seconds=uptime,
            active_sessions=self._metrics.active_sessions,
            event_count=self._metrics.event_count,
            last_error=self._metrics.last_error,
        )

    def _read_uptime(self) -> float:
        try:
            import psutil
            return psutil.boot_time()
        except Exception:
            return 0.0

    @property
    def metrics(self) -> RuntimeMetrics:
        return self._metrics

    def get_summary(self) -> str:
        m = self._metrics
        return (
            f"CPU: {m.cpu_percent:.1f}% | "
            f"Memory: {m.memory_percent:.1f}% | "
            f"Uptime: {m.uptime_seconds:.0f}s"
        )
