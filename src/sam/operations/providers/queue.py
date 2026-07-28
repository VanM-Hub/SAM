"""
QueueMonitor — Tracking antrean kerja + throughput untuk RuntimeProvider.

Menyediakan data queue depth, throughput, latency, operation count.
Auto-hook via TelemetryService.subscribe() — semua event tercatat otomatis.

Pola:
  with queue_monitor.track("observe"):
      # operasi apapun
      ...
  # -> otomatis: depth++, latency dihitung, throughput di-update

TIDAK ada panggilan manual track_operation().
"""

import contextlib
import time
import structlog
from dataclasses import dataclass, field
from typing import List, Optional, Iterator


logger = structlog.get_logger()


@dataclass
class OperationDetail:
    """Detail satu operasi yang sedang atau sudah selesai."""
    name: str
    started_at: float
    finished_at: Optional[float] = None
    duration_ms: Optional[float] = None

    @property
    def is_active(self) -> bool:
        return self.finished_at is None


@dataclass
class QueueStats:
    """Statistik antrean dalam satu window."""
    depth: int
    max_depth: int
    avg_depth: float
    throughput: float            # operasi/detik
    active_operations: int = 0
    avg_latency_ms: float = 0.0
    peak_latency_ms: float = 0.0
    total_completed: int = 0
    operations_last_minute: int = 0  # operasi dalam 60 detik terakhir
    window_seconds: float = 60.0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "depth": self.depth,
            "max_depth": self.max_depth,
            "avg_depth": self.avg_depth,
            "throughput": self.throughput,
            "active_operations": self.active_operations,
            "avg_latency_ms": round(self.avg_latency_ms, 1),
            "peak_latency_ms": round(self.peak_latency_ms, 1),
            "total_completed": self.total_completed,
            "operations_last_minute": self.operations_last_minute,
            "window_seconds": self.window_seconds,
            "timestamp": self.timestamp,
        }

    @property
    def summary(self) -> str:
        """Human-readable summary — untuk ConversationObject facts."""
        parts = []
        if self.depth == 0 and self.active_operations == 0:
            parts.append("System idle")
        else:
            if self.depth > 0:
                parts.append("Queue: {} pending".format(self.depth))
            if self.active_operations > 0:
                parts.append("{} active".format(self.active_operations))
            if self.throughput > 0:
                parts.append("{:.1f} ops/s".format(self.throughput))
            if self.avg_latency_ms > 0:
                parts.append("avg {:.0f}ms".format(self.avg_latency_ms))

        if not parts:
            return "System idle"
        return " | ".join(parts)

    @property
    def high_workload(self) -> bool:
        """Deteksi workload tinggi."""
        return self.depth > 5 or self.active_operations > 3


class QueueMonitor:
    """Monitor antrean internal SAM — depth, throughput, latency, pattern.

    Otomatis: setiap TelemetryEvent yang lewat TelemetryService dicatat.
    Manual: context manager track() untuk operasi spesifik.

    INI ADALAH IMPLEMENTATION DETAIL — tidak terlihat oleh caller.
    """

    def __init__(self, window_seconds: float = 60.0):
        self._window_seconds = window_seconds
        # Event tracking — timestamp setiap operasi untuk throughput
        self._operations: List[float] = []
        # Depth tracking — snapshot depth
        self._depth_history: List[int] = []
        self._current_depth: int = 0
        self._max_depth: int = 0
        # Operation details — latency tracking
        self._active: dict = {}       # name -> OperationDetail
        self._completed: List[float] = []   # latency_ms history (untuk avg/peak)
        self._total_completed: int = 0
        # Hook flag
        self._telemetry_hooked = False

    # ====================================================================
    # Context Manager — AUTOMATIC tracking
    # ====================================================================

    @contextlib.contextmanager
    def track(self, operation_name: str = "unknown") -> Iterator[None]:
        """Context manager: wrap operasi → otomatis depth + latency + throughput.

        Developer TIDAK perlu panggil operation_started/finished.
        Cukup:
            with queue_monitor.track("observe"):
                ...
        """
        started = time.time()
        self.operation_started(operation_name)
        try:
            yield
        except Exception:
            # Catat tetap finished meskipun error
            elapsed = (time.time() - started) * 1000
            self.operation_finished(operation_name, elapsed)
            raise
        else:
            elapsed = (time.time() - started) * 1000
            self.operation_finished(operation_name, elapsed)

    # ====================================================================
    # Telemetry hook — auto-track semua event
    # ====================================================================

    def hook_telemetry(self, telemetry):
        """Pasang subscriber ke TelemetryService — otomatis track semua event.

        Dipanggil sekali saat SAM.__init__().
        Setiap event yang lewat TelemetryService tercatat sebagai operasi.
        """
        if self._telemetry_hooked:
            return
        self._telemetry_hooked = True

        def on_event(event):
            import inspect
            caller_name = "unknown"
            try:
                frame = inspect.currentframe()
                if frame and frame.f_back and frame.f_back.f_code:
                    caller_name = frame.f_back.f_code.co_name
            except Exception:
                pass

            event_name = getattr(event, 'type', None)
            event_str = event_name.value if event_name else caller_name

            # Catat sebagai operasi (point-in-time: satu event = satu operasi selesai)
            self.operation_started(event_str)
            self.operation_finished(event_str, 0.0)

        telemetry.subscribe(on_event)
        logger.info("queue_monitor.hooked_to_telemetry")

    # ====================================================================
    # Event tracking — INTERNAL (jangan panggil langsung)
    # ====================================================================

    def operation_started(self, name: str = "unknown"):
        """Catat satu operasi dimulai. Dipanggil oleh track() atau hook."""
        now = time.time()
        self._operations.append(now)
        self._current_depth += 1
        if self._current_depth > self._max_depth:
            self._max_depth = self._current_depth
        self._active[name] = OperationDetail(name=name, started_at=now)
        self._evict_old(now)

    def operation_finished(self, name: str, duration_ms: float):
        """Catat satu operasi selesai. Dipanggil oleh track() atau hook."""
        self._current_depth = max(0, self._current_depth - 1)
        self._depth_history.append(self._current_depth)

        # Update latency
        self._completed.append(duration_ms)
        self._total_completed += 1
        if len(self._completed) > 1000:
            self._completed = self._completed[-500:]

        # Update active tracking
        if name in self._active:
            detail = self._active.pop(name)
            detail.finished_at = time.time()
            detail.duration_ms = duration_ms

    # ====================================================================
    # Query
    # ====================================================================

    def get_depth(self) -> int:
        """Queue depth saat ini."""
        return self._current_depth

    def get_throughput(self) -> float:
        """Throughput dalam operasi/detik."""
        now = time.time()
        self._evict_old(now)
        if not self._operations or self._window_seconds <= 0:
            return 0.0
        elapsed = now - self._operations[0]
        if elapsed <= 0:
            return 0.0
        return len(self._operations) / elapsed

    def get_active_operations(self) -> int:
        """Jumlah operasi yang sedang aktif."""
        return len(self._active)

    def get_operations_last_minute(self) -> int:
        """Jumlah operasi dalam 60 detik terakhir."""
        now = time.time()
        cutoff = now - 60.0
        return sum(1 for t in self._operations if t > cutoff)

    def get_operation_stats(self) -> dict:
        """Detail operasi untuk technical_details().

        Returns dict dengan key:
          - depth: queue depth
          - throughput: ops/s
          - active_operations: jumlah operasi aktif
          - avg_latency_ms: rata-rata latensi (history)
          - peak_latency_ms: peak latensi (history)
          - total_completed: total operasi selesai
          - operations_last_minute: operasi dalam 60 detik
          - active_names: daftar nama operasi aktif
        """
        # Latency stats
        latencies = self._completed
        avg_lat = sum(latencies) / len(latencies) if latencies else 0.0
        peak_lat = max(latencies) if latencies else 0.0

        return {
            "depth": self._current_depth,
            "throughput": self.get_throughput(),
            "active_operations": len(self._active),
            "avg_latency_ms": round(avg_lat, 1),
            "peak_latency_ms": round(peak_lat, 1),
            "total_completed": self._total_completed,
            "operations_last_minute": self.get_operations_last_minute(),
            "active_names": list(self._active.keys()),
        }

    def get_stats(self, window_seconds: Optional[float] = None) -> QueueStats:
        """Statistik queue dalam window tertentu."""
        window = window_seconds or self._window_seconds
        now = time.time()
        cutoff = now - window

        # Hitung throughput dalam window
        recent_ops = [t for t in self._operations if t > cutoff]
        throughput = 0.0
        if recent_ops and window > 0:
            elapsed = now - recent_ops[0]
            if elapsed > 0:
                throughput = len(recent_ops) / elapsed

        # Depth stats
        recent_depth = [d for d in self._depth_history if d is not None]
        avg_depth = 0.0
        if recent_depth:
            avg_depth = sum(recent_depth) / len(recent_depth)

        # Latency stats
        latencies = self._completed
        avg_lat = sum(latencies) / len(latencies) if latencies else 0.0
        peak_lat = max(latencies) if latencies else 0.0

        return QueueStats(
            depth=self._current_depth,
            max_depth=self._max_depth,
            avg_depth=avg_depth,
            throughput=throughput,
            active_operations=len(self._active),
            avg_latency_ms=avg_lat,
            peak_latency_ms=peak_lat,
            total_completed=self._total_completed,
            operations_last_minute=self.get_operations_last_minute(),
            window_seconds=window,
        )

    def reset(self):
        """Reset semua data."""
        self._operations.clear()
        self._depth_history.clear()
        self._completed.clear()
        self._active.clear()
        self._current_depth = 0
        self._max_depth = 0
        self._total_completed = 0
        logger.debug("queue_monitor.reset")

    # ====================================================================
    # Internal
    # ====================================================================

    def _evict_old(self, now: float):
        """Hapus entry di luar window."""
        cutoff = now - self._window_seconds
        self._operations = [t for t in self._operations if t > cutoff]
