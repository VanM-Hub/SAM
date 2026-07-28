"""
AnomalyDetector — Mendeteksi keadaan abnormal dari Runtime, Queue, Workspace, Telemetry.

Output:
  Anomaly — severity, confidence, evidence
"""

import structlog
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


logger = structlog.get_logger()


# Thresholds — sama dengan RCA untuk konsistensi
CPU_HIGH = 80.0
MEMORY_HIGH = 85.0
QUEUE_GROWING = 5
QUEUE_LATENCY_HIGH = 2000  # ms
DISK_NEAR_FULL = 85.0
TEMP_HIGH_COUNT = 500
TEMP_HIGH_MB = 200
CACHE_HIGH_MB = 500
FILE_COUNT_HIGH = 5000
UPTIME_LOW = 300  # detik


@dataclass
class Anomaly:
    """Satu anomali yang terdeteksi."""
    type: str               # cpu_spike, memory_leak, queue_growth, disk_exhaustion, dll
    severity: str           # information, warning, critical
    confidence: float       # 0.0 - 1.0
    evidence: List[str]     # Bukti konkret
    value: Any = None       # Nilai terdeteksi
    threshold: Any = None   # Threshold yang dilanggar
    detail: str = ""        # Penjelasan tambahan
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "severity": self.severity,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "value": self.value,
            "threshold": self.threshold,
            "detail": self.detail,
            "timestamp": self.timestamp,
        }


class AnomalyDetector:
    """Mendeteksi anomali dari semua sumber observasi."""

    def __init__(self, runtime_provider=None, workspace_provider=None, telemetry_service=None):
        self._rp = runtime_provider
        self._wp = workspace_provider
        self._telemetry = telemetry_service

    def detect_all(self) -> List[Anomaly]:
        """Deteksi semua anomali dari sumber yang tersedia.

        Returns:
            List Anomaly — kosong jika tidak ada yang abnormal.
        """
        anomalies = []

        # Runtime
        if self._rp:
            snap = self._rp.get_latest()
            if snap:
                anomalies.extend(self._detect_runtime(snap))

        # Workspace
        if self._wp:
            ws = self._wp.observe()
            anomalies.extend(self._detect_workspace(ws))

        logger.info("anomaly_detection_completed",
            detected=len(anomalies),
            severities=[a.severity for a in anomalies],
        )
        return anomalies

    def detect(self, source: str = "all") -> List[Anomaly]:
        """Deteksi anomali dari sumber tertentu.

        Args:
            source: "runtime", "workspace", "queue", "all"
        """
        if source == "runtime":
            if not self._rp:
                return []
            snap = self._rp.get_latest()
            return self._detect_runtime(snap) if snap else []
        elif source == "workspace":
            if not self._wp:
                return []
            ws = self._wp.observe()
            return self._detect_workspace(ws)
        elif source == "queue":
            if not self._rp:
                return []
            snap = self._rp.get_latest()
            return self._detect_queue(snap) if snap else []
        return self.detect_all()

    def _detect_runtime(self, snap) -> List[Anomaly]:
        anomalies = []

        # CPU spike
        cpu = snap.cpu_percent
        if cpu > CPU_HIGH:
            anomalies.append(Anomaly(
                type="cpu_spike",
                severity="warning" if cpu < 95 else "critical",
                confidence=min(0.95, 0.5 + (cpu - CPU_HIGH) / 100),
                evidence=["CPU at {:.1f}% (threshold: {:.0f}%)".format(cpu, CPU_HIGH)],
                value=cpu,
                threshold=CPU_HIGH,
                detail="CPU exceeds normal range. Queue depth: {}".format(snap.queue_depth),
            ))

        # Memory high
        mem = snap.memory_percent
        if mem > MEMORY_HIGH:
            anomalies.append(Anomaly(
                type="memory_high",
                severity="warning" if mem < 95 else "critical",
                confidence=min(0.9, 0.5 + (mem - MEMORY_HIGH) / 100),
                evidence=["Memory at {:.1f}% (threshold: {:.0f}%)".format(mem, MEMORY_HIGH)],
                value=mem,
                threshold=MEMORY_HIGH,
            ))

        # Uptime sangat rendah — recent restart
        if snap.uptime_seconds < UPTIME_LOW and snap.uptime_seconds > 0:
            anomalies.append(Anomaly(
                type="recent_restart",
                severity="information",
                confidence=0.9,
                evidence=["System started {:.0f}s ago".format(snap.uptime_seconds)],
                value=snap.uptime_seconds,
                threshold=UPTIME_LOW,
                detail="Recent restart may explain CPU/memory spikes",
            ))

        # Queue
        anomalies.extend(self._detect_queue(snap))

        return anomalies

    def _detect_queue(self, snap) -> List[Anomaly]:
        anomalies = []

        # Queue growth
        depth = snap.queue_depth
        if depth > QUEUE_GROWING:
            anomalies.append(Anomaly(
                type="queue_growth",
                severity="warning" if depth < 20 else "critical",
                confidence=min(0.95, 0.5 + depth / 50),
                evidence=["Queue depth: {} (threshold: {})".format(depth, QUEUE_GROWING)],
                value=depth,
                threshold=QUEUE_GROWING,
                detail="{} pending, {} active, {:.1f} ops/s throughput".format(
                    depth, snap.active_operations, snap.throughput
                ),
            ))

        # High latency
        latency = snap.avg_latency_ms
        if latency > QUEUE_LATENCY_HIGH:
            anomalies.append(Anomaly(
                type="high_latency",
                severity="warning",
                confidence=min(0.9, 0.5 + latency / 10000),
                evidence=["Avg latency: {:.0f}ms (threshold: {}ms)".format(latency, QUEUE_LATENCY_HIGH)],
                value=latency,
                threshold=QUEUE_LATENCY_HIGH,
            ))

        return anomalies

    def _detect_workspace(self, ws) -> List[Anomaly]:
        anomalies = []

        # Disk exhaustion
        disk = ws.disk
        if disk.percent > DISK_NEAR_FULL:
            anomalies.append(Anomaly(
                type="disk_exhaustion",
                severity="warning" if disk.percent < 95 else "critical",
                confidence=min(0.95, 0.5 + (disk.percent - DISK_NEAR_FULL) / 100),
                evidence=["Disk at {:.1f}% ({:.1f} GB / {:.1f} GB)".format(
                    disk.percent, disk.used_gb, disk.total_gb
                )],
                value=disk.percent,
                threshold=DISK_NEAR_FULL,
            ))

        # Database unavailable
        db = ws.database
        if db.status.lower() == "unavailable":
            anomalies.append(Anomaly(
                type="database_unavailable",
                severity="critical",
                confidence=0.9,
                evidence=["Database status: unavailable"],
                value=db.status,
                threshold="available",
            ))

        # Cache explosion
        cache = ws.cache
        if cache.size_mb > CACHE_HIGH_MB:
            anomalies.append(Anomaly(
                type="cache_explosion",
                severity="information",
                confidence=min(0.85, 0.5 + cache.size_mb / 2000),
                evidence=["Cache at {:.1f} MB ({} files)".format(cache.size_mb, cache.file_count)],
                value=cache.size_mb,
                threshold=CACHE_HIGH_MB,
            ))

        # Temp accumulation
        temp = ws.temp
        if temp.count > TEMP_HIGH_COUNT or temp.size_mb > TEMP_HIGH_MB:
            anomalies.append(Anomaly(
                type="temp_accumulation",
                severity="information",
                confidence=min(0.8, 0.5 + temp.count / 2000),
                evidence=["Temp files: {} ({:.1f} MB)".format(temp.count, temp.size_mb)],
                value=temp.count if temp.count > TEMP_HIGH_COUNT else temp.size_mb,
                threshold=TEMP_HIGH_COUNT if temp.count > TEMP_HIGH_COUNT else TEMP_HIGH_MB,
            ))

        # File count tinggi
        ws_fc = getattr(ws.workspace, 'file_count', 0)
        if ws_fc > FILE_COUNT_HIGH:
            anomalies.append(Anomaly(
                type="high_file_count",
                severity="information",
                confidence=min(0.7, 0.5 + ws_fc / 20000),
                evidence=["File count: {} (threshold: {})".format(ws_fc, FILE_COUNT_HIGH)],
                value=ws_fc,
                threshold=FILE_COUNT_HIGH,
            ))

        return anomalies
