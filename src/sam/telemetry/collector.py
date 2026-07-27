"""
Metrics Collector — Phase 1

Mengumpulkan CPU, memory, uptime secara periodik.
Terintegrasi dengan Runtime Coordinator dan TelemetryService.
"""

import asyncio
import structlog
from datetime import datetime
from .models import RuntimeMetrics

logger = structlog.get_logger()


class MetricsCollector:
    """Metrics Collector — kumpulkan metrics runtime setiap interval.

    Args:
        coordinator: RuntimeCoordinator instance (memiliki .telemetry dan .start_time).
        interval: Interval koleksi dalam detik (default 10).
    """

    def __init__(self, coordinator, interval: int = 10):
        self.coordinator = coordinator
        self.interval = interval
        self._running = False

    async def start(self) -> None:
        """Mulai loop koleksi metrics periodik."""
        self._running = True
        logger.info("metrics_collector_started", interval=self.interval)

        while self._running:
            try:
                metrics = await self.collect()
                if hasattr(self.coordinator, "telemetry") and self.coordinator.telemetry:
                    self.coordinator.telemetry.record_metrics(metrics)
            except Exception as e:
                logger.error("metrics_collection_failed", error=str(e))
            await asyncio.sleep(self.interval)

    async def stop(self) -> None:
        """Hentikan koleksi metrics."""
        self._running = False
        logger.info("metrics_collector_stopped")

    async def collect(self) -> RuntimeMetrics:
        """Kumpulkan metrics Runtime saat ini.

        Returns:
            RuntimeMetrics snapshot dengan data real-time.
        """
        cpu = await self._get_cpu()
        memory = await self._get_memory()
        uptime = await self._get_uptime()

        return RuntimeMetrics(
            cpu_percent=cpu,
            memory_mb=memory,
            uptime_seconds=uptime,
            workflow_count=2,   # simulasi — akan diganti dengan real counter
            plugin_count=14,    # simulasi — akan diganti dengan real counter
            health_score=100.0,  # placeholder
        )

    async def _get_cpu(self) -> float:
        """Ambil CPU utilisation via psutil.

        Falls back ke 0.0 jika psutil tidak terinstall.
        """
        try:
            import psutil
            return psutil.cpu_percent(interval=0.1)
        except ImportError:
            return 0.0

    async def _get_memory(self) -> float:
        """Ambil memory usage dalam MB.

        Falls back ke 0.0 jika psutil tidak terinstall.
        """
        try:
            import psutil
            return psutil.virtual_memory().used / (1024 * 1024)
        except ImportError:
            return 0.0

    async def _get_uptime(self) -> float:
        """Ambil uptime coordinator dalam detik."""
        if hasattr(self.coordinator, "start_time") and self.coordinator.start_time:
            return (datetime.utcnow() - self.coordinator.start_time).total_seconds()
        return 0.0
