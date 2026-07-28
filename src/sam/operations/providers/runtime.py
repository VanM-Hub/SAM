"""
RuntimeProvider — Observation Provider untuk data runtime real-time.

Menyediakan CPU, memory, proses, queue, throughput.
Source data: psutil (polling) + SAM internal (queue/throughput).

Alur:
  1. start() → loop asyncio setiap interval → poll() → emit event → store snapshot
  2. poll() → snapshot CPU + memory + (opsional: proses, disk, network)
  3. get_latest() → snapshot terakhir
  4. Integrasi dengan TelemetryService — setiap snapshot jadi event METRIC

Pola: Observer + Singleton-ish (satu provider per SAM instance).
"""

import asyncio
import structlog
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

import psutil

from .queue import QueueMonitor, QueueStats
from .workspace import WorkspaceProvider

logger = structlog.get_logger()


# ============================================================================
# Models
# ============================================================================

@dataclass
class CPUSnapshot:
    """Data CPU dalam satu titik waktu."""
    percent: float              # CPU usage keseluruhan (%)
    per_cpu: List[float]        # Per-core
    count: int                  # Jumlah core (logical)
    timestamp: float            # Unix timestamp

    def to_dict(self) -> dict:
        return {
            "percent": self.percent,
            "per_cpu": self.per_cpu,
            "count": self.count,
            "timestamp": self.timestamp,
        }


@dataclass
class MemorySnapshot:
    """Data memory dalam satu titik waktu."""
    rss: int                    # RSS dalam bytes
    vms: int                    # VMS dalam bytes
    available: int              # Memory tersedia (bytes)
    percent: float              # Usage %
    total: int                  # Total RAM (bytes)
    timestamp: float

    def to_dict(self) -> dict:
        return {
            "rss": self.rss,
            "vms": self.vms,
            "available": self.available,
            "percent": self.percent,
            "total": self.total,
            "timestamp": self.timestamp,
        }


@dataclass
class RuntimeSnapshot:
    """Snapshot lengkap runtime dalam satu titik polling."""
    cpu: CPUSnapshot
    memory: MemorySnapshot
    queue_depth: int = 0
    throughput: float = 0.0     # Operasi/detik dalam window
    uptime_seconds: float = 0.0
    timestamp: float = field(default_factory=time.time)

    # Queue stats dari QueueMonitor
    active_operations: int = 0
    avg_latency_ms: float = 0.0
    peak_latency_ms: float = 0.0
    total_completed: int = 0
    operations_last_minute: int = 0

    def to_dict(self) -> dict:
        return {
            "cpu": self.cpu.to_dict(),
            "memory": self.memory.to_dict(),
            "queue_depth": self.queue_depth,
            "throughput": self.throughput,
            "active_operations": self.active_operations,
            "avg_latency_ms": round(self.avg_latency_ms, 1),
            "peak_latency_ms": round(self.peak_latency_ms, 1),
            "total_completed": self.total_completed,
            "operations_last_minute": self.operations_last_minute,
            "uptime_seconds": self.uptime_seconds,
            "timestamp": self.timestamp,
        }

    @property
    def cpu_percent(self) -> float:
        return self.cpu.percent

    @property
    def memory_percent(self) -> float:
        return self.memory.percent

    @property
    def queue_status(self) -> str:
        """Status queue: idle / processing / overloaded / growing / healthy."""
        if self.queue_depth == 0 and self.active_operations == 0:
            return "idle"
        if self.queue_depth > 5 or self.active_operations > 3:
            return "overloaded"
        if self.queue_depth > 0 and self.throughput > 0:
            return "processing"
        if self.queue_depth > 2:
            return "growing"
        return "healthy"

    @property
    def summary(self) -> str:
        parts = []
        parts.append("CPU: {:.1f}%".format(self.cpu.percent))
        parts.append("Memory: {:.1f}%".format(self.memory.percent))
        if self.queue_depth > 0 or self.active_operations > 0:
            parts.append("Queue: {}".format(self.queue_depth))
            parts.append("Active: {}".format(self.active_operations))
            parts.append("{:.1f} ops/s".format(self.throughput))
        else:
            parts.append("System idle")
        return " | ".join(parts)


# ============================================================================
# Provider — data source untuk ConversationObject
# ============================================================================

class RuntimeProvider:
    """Provider data runtime real-time — CPU, memory, queue, throughput.

    Bisa di-start/stop sebagai background task.
    Data polling disimpan sebagai snapshot terakhir + history (opsional).
    """

    def __init__(self, interval: float = 5.0, telemetry=None):
        """
        Args:
            interval: Polling interval dalam detik (default 5).
            telemetry: TelemetryService instance untuk emit event.
        """
        self._interval = interval
        self._telemetry = telemetry
        self._queue_monitor = QueueMonitor()  # internal — satu-satunya QueueMonitor
        self._workspace_provider = WorkspaceProvider()
        self._latest_workspace = None
        self._latest: Optional[RuntimeSnapshot] = None
        self._history: List[RuntimeSnapshot] = []  # ring buffer, max 1000
        self._max_history = 1000
        self._running = False
        self._start_time: Optional[float] = None
        self._task: Optional[asyncio.Task] = None

        # Queue & throughput tracking (legacy — tetap jalan)
        self._queue_depth = 0
        self._throughput_window: List[float] = []
        self._throughput_window_seconds = 60.0

    # ====================================================================
    # Lifecycle
    # ====================================================================

    async def start(self):
        """Mulai polling periodik sebagai background task."""
        if self._running:
            logger.warning("runtime_provider.already_running")
            return

        self._running = True
        self._start_time = time.time()

        # Ambil snapshot pertama langsung
        try:
            self._latest = self._poll()
            self._add_history(self._latest)
            self._emit_telemetry(self._latest)
            logger.info("runtime_provider.started", interval=self._interval)
        except Exception as e:
            logger.error("runtime_provider.first_poll_failed", error=str(e))

        # Mulai loop
        self._task = asyncio.create_task(self._loop())

    async def stop(self):
        """Hentikan polling."""
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None
        logger.info("runtime_provider.stopped")

    # ====================================================================
    # Public API
    # ====================================================================

    def get_latest(self) -> Optional[RuntimeSnapshot]:
        """Snapshot terakhir dari polling."""
        return self._latest

    def get_history(self, limit: int = 100) -> List[RuntimeSnapshot]:
        """History snapshot (terbaru dulu)."""
        return list(reversed(self._history[-limit:]))

    def get_stats(self) -> Dict[str, Any]:
        """Statistik provider."""
        return {
            "running": self._running,
            "interval": self._interval,
            "history_count": len(self._history),
            "uptime": (time.time() - self._start_time) if self._start_time else 0,
            "latest": self._latest.to_dict() if self._latest else None,
        }

    # Queue tracking — dipanggil oleh sistem luar
    def track_queue(self, depth: int):
        """Update queue depth (dari ConversationObject atau QueueMonitor)."""
        self._queue_depth = depth

    def track_operation(self):
        """Catat satu operasi untuk throughput."""
        now = time.time()
        self._throughput_window.append(now)
        # Evict entries older than window
        cutoff = now - self._throughput_window_seconds
        self._throughput_window = [t for t in self._throughput_window if t > cutoff]

    def get_throughput(self) -> float:
        """Hitung throughput dalam ops/detik."""
        now = time.time()
        cutoff = now - self._throughput_window_seconds
        recent = [t for t in self._throughput_window if t > cutoff]
        if not recent or self._throughput_window_seconds <= 0:
            return 0.0
        # Hitung rate: count / window (atau sejak entry pertama)
        elapsed = now - recent[0]
        if elapsed <= 0:
            return 0.0
        return len(recent) / elapsed

    # ====================================================================
    # Internal
    # ====================================================================

    async def _loop(self):
        """Loop polling periodik."""
        while self._running:
            await asyncio.sleep(self._interval)
            try:
                snapshot = self._poll()
                self._latest = snapshot
                self._add_history(snapshot)
                self._emit_telemetry(snapshot)
            except Exception as e:
                logger.error("runtime_provider.poll_failed", error=str(e))

    def get_workspace(self):
        """Dapatkan snapshot workspace terbaru (lazy-observe).

        Juga trigger _poll() jika belum ada data runtime.
        """
        try:
            self._latest_workspace = self._workspace_provider.observe()
            # Trigger runtime poll jika belum ada
            if self._latest is None:
                self._latest = self._poll()
        except Exception as e:
            logger.warning("runtime_provider.workspace_error", error=str(e))
        return self._latest_workspace

    def _poll(self) -> RuntimeSnapshot:
        """Poll data CPU + memory + queue dari psutil + QueueMonitor."""
        # CPU
        cpu_percent = psutil.cpu_percent(interval=None)
        per_cpu = psutil.cpu_percent(interval=None, percpu=True)
        cpu_count = psutil.cpu_count(logical=True)
        now = time.time()

        cpu = CPUSnapshot(
            percent=cpu_percent,
            per_cpu=per_cpu,
            count=cpu_count,
            timestamp=now,
        )

        # Memory
        mem = psutil.virtual_memory()
        proc = psutil.Process()
        memory = MemorySnapshot(
            rss=proc.memory_info().rss,
            vms=proc.memory_info().vms,
            available=mem.available,
            percent=mem.percent,
            total=mem.total,
            timestamp=now,
        )

        # Queue & throughput — PRIORITAS QueueMonitor
        qm = self._queue_monitor
        queue_depth = qm.get_depth() if qm else self._queue_depth
        throughput = qm.get_throughput() if qm else self.get_throughput()
        ops = qm.get_operation_stats() if qm else {}

        # Uptime
        uptime = (now - self._start_time) if self._start_time else 0.0

        return RuntimeSnapshot(
            cpu=cpu,
            memory=memory,
            queue_depth=queue_depth,
            throughput=throughput,
            active_operations=ops.get("active_operations", 0),
            avg_latency_ms=ops.get("avg_latency_ms", 0.0),
            peak_latency_ms=ops.get("peak_latency_ms", 0.0),
            total_completed=ops.get("total_completed", 0),
            operations_last_minute=ops.get("operations_last_minute", 0),
            uptime_seconds=uptime,
            timestamp=now,
        )

    def _add_history(self, snapshot: RuntimeSnapshot):
        """Simpan ke ring buffer."""
        self._history.append(snapshot)
        if len(self._history) > self._max_history:
            self._history.pop(0)

    def _emit_telemetry(self, snapshot: RuntimeSnapshot):
        """Kirim event ke TelemetryService."""
        if not self._telemetry:
            return

        try:
            from ...telemetry.event import TelemetryEvent, EventSeverity, EventCategory
            from ...telemetry.event_type import TelemetryEventType
            from ...telemetry.component import Component

            event = TelemetryEvent(
                type=TelemetryEventType.SYSTEM_BOOT,  # reuse — tidak ada METRIC type
                component=Component.OPERATIONS,
                severity=EventSeverity.INFO,
                category=EventCategory.RESOURCE,
                message=f"Runtime snapshot: {snapshot.summary}",
                metadata=snapshot.to_dict(),
            )
            self._telemetry.emit(event)
        except Exception as e:
            logger.debug("runtime_provider.telemetry_emit_failed", error=str(e))

    async def _emit_telemetry_compat(self, snapshot: RuntimeSnapshot):
        """Fallback: pakai emit_event compat adapter."""
        if not self._telemetry:
            return
        try:
            self._telemetry.emit_event(
                event_name="runtime.snapshot",
                component="operations",
                severity="info",
                category="resource",
                payload=snapshot.to_dict(),
            )
        except Exception as e:
            logger.debug("runtime_provider.telemetry_compat_failed", error=str(e))
