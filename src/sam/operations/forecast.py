"""
ForecastEngine — Forecasting berbasis evidence dari time-series data.

Hanya menghasilkan forecast jika tersedia cukup data historis.
Jika tidak: "Forecast unavailable. Need additional historical observations."
"""

import structlog
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


logger = structlog.get_logger()


@dataclass
class Forecast:
    """Satu prediksi untuk satu metrik."""
    metric: str         # cpu_percent, memory_percent, disk_percent, queue_depth, workspace_files
    prediction: Any     # Nilai yang diprediksi
    confidence: float   # 0.0 - 1.0
    time_horizon: str   # "1h", "6h", "24h", "7d"
    supporting_evidence: List[str] = field(default_factory=list)
    current_value: Any = None
    trend: str = "stable"  # rising, falling, stable, unknown
    detail: str = ""

    def to_text(self) -> str:
        return "{metric}: {prediction} ({horizon}, {confidence:.0f}%)".format(
            metric=self.metric.replace("_", " ").title(),
            prediction=self.prediction,
            horizon=self.time_horizon,
            confidence=self.confidence * 100,
        )


class ForecastEngine:
    """Forecasting — hanya dengan time-series data yang cukup.

    Saat ini: threshold-based projection (karena data historis terbatas).
    Future: sama dengan time-series dari TelemetryService.
    """

    def __init__(self, runtime_provider=None, workspace_provider=None):
        self._rp = runtime_provider
        self._wp = workspace_provider

    def forecast_all(self) -> List[Forecast]:
        """Forecast semua metrik yang tersedia."""
        forecasts = []

        if self._rp:
            snap = self._rp.get_latest()
            if snap:
                forecasts.extend(self._forecast_runtime(snap))

        if self._wp:
            ws = self._wp.observe()
            forecasts.extend(self._forecast_workspace(ws))

        if not forecasts:
            forecasts.append(Forecast(
                metric="general",
                prediction="Forecast unavailable.",
                confidence=0.0,
                time_horizon="N/A",
                supporting_evidence=["No time-series data available"],
                trend="unknown",
                detail="Need additional historical observations.",
            ))

        logger.info("forecast_completed",
            forecasts=len(forecasts),
            metrics=[f.metric for f in forecasts],
        )
        return forecasts

    def forecast(self, metric: str = "all") -> List[Forecast]:
        """Forecast spesifik metrik."""
        if metric == "all":
            return self.forecast_all()

        all_f = self.forecast_all()
        return [f for f in all_f if f.metric == metric] or [
            Forecast(
                metric=metric,
                prediction="Forecast unavailable.",
                confidence=0.0,
                time_horizon="N/A",
                supporting_evidence=["No time-series data for '{}'".format(metric)],
                trend="unknown",
                detail="Need historical observations.",
            )
        ]

    def _forecast_runtime(self, snap) -> List[Forecast]:
        forecasts = []

        cpu = snap.cpu_percent
        if cpu > 50:
            # CPU tinggi — proyeksi ke depan
            next_h = min(100, cpu * 1.1)  # estimasi 10% growth
            forecasts.append(Forecast(
                metric="cpu_percent",
                prediction="{:.1f}%".format(next_h),
                confidence=0.4,
                time_horizon="1h",
                supporting_evidence=["CPU currently at {:.1f}%".format(cpu)],
                current_value=cpu,
                trend="rising" if cpu > 70 else "stable",
                detail="CPU may continue rising if current workload persists",
            ))
        else:
            forecasts.append(Forecast(
                metric="cpu_percent",
                prediction="{:.1f}% (stable)".format(cpu),
                confidence=0.6,
                time_horizon="1h",
                supporting_evidence=["CPU within normal range ({:.1f}%)".format(cpu)],
                current_value=cpu,
                trend="stable",
                detail="No significant CPU change expected",
            ))

        mem = snap.memory_percent
        if mem > MEMORY_TREND_THRESHOLD:
            next_mem = min(100, mem * 1.05)
            forecasts.append(Forecast(
                metric="memory_percent",
                prediction="{:.1f}%".format(next_mem),
                confidence=0.35,
                time_horizon="6h",
                supporting_evidence=["Memory at {:.1f}%".format(mem)],
                current_value=mem,
                trend="rising",
                detail="Memory usage expected to increase if trend continues",
            ))
        else:
            forecasts.append(Forecast(
                metric="memory_percent",
                prediction="{:.1f}% (stable)".format(mem),
                confidence=0.55,
                time_horizon="6h",
                supporting_evidence=["Memory within range ({:.1f}%)".format(mem)],
                current_value=mem,
                trend="stable",
            ))

        # Queue
        depth = snap.queue_depth
        if depth > 0:
            growth_est = depth * 1.5 if snap.queue_status in ("growing", "overloaded") else depth * 1.1
            forecasts.append(Forecast(
                metric="queue_depth",
                prediction="{:.0f} pending".format(growth_est),
                confidence=0.3 if snap.queue_status == "growing" else 0.5,
                time_horizon="30m",
                supporting_evidence=["Queue depth: {} (status: {})".format(depth, snap.queue_status)],
                current_value=depth,
                trend="rising" if snap.queue_status in ("growing", "overloaded") else "stable",
                detail="Queue may {} in the next 30 minutes".format("grow" if snap.queue_status in ("growing", "overloaded") else "drain"),
            ))
        else:
            forecasts.append(Forecast(
                metric="queue_depth",
                prediction="0 (idle)",
                confidence=0.8,
                time_horizon="1h",
                supporting_evidence=["Queue is idle"],
                current_value=0,
                trend="stable",
            ))

        return forecasts

    def _forecast_workspace(self, ws) -> List[Forecast]:
        forecasts = []

        # Disk
        disk_pct = ws.disk.percent
        if disk_pct > 50:
            # Proyeksi: disk bisa penuh dalam ... 
            remaining_pct = 100 - disk_pct
            days_est = int(remaining_pct / max(0.5, (disk_pct - 50) / 30))  # estimasi kasar
            horizon = "{}d".format(max(1, days_est))
            forecasts.append(Forecast(
                metric="disk_percent",
                prediction="{:.1f}% (estimated {} days until full)".format(min(100, disk_pct + remaining_pct * 0.3), max(1, days_est)),
                confidence=0.3,
                time_horizon=horizon,
                supporting_evidence=["Disk at {:.1f}% ({:.1f} GB / {:.1f} GB)".format(
                    disk_pct, ws.disk.used_gb, ws.disk.total_gb
                )],
                current_value=disk_pct,
                trend="rising" if disk_pct > 70 else "stable",
                detail="Disk usage trending upward",
            ))
        else:
            forecasts.append(Forecast(
                metric="disk_percent",
                prediction="{:.1f}% (adequate)".format(disk_pct),
                confidence=0.6,
                time_horizon="7d",
                supporting_evidence=["Disk usage moderate ({:.1f}%)".format(disk_pct)],
                current_value=disk_pct,
                trend="stable",
            ))

        # Workspace file count
        fc = ws.workspace.file_count
        if fc > 1000:
            forecasts.append(Forecast(
                metric="workspace_file_count",
                prediction="{:.0f} files (estimating growth)".format(fc * 1.1),
                confidence=0.25,
                time_horizon="7d",
                supporting_evidence=["Workspace: {} files ({:.1f} MB)".format(fc, ws.workspace.size_mb)],
                current_value=fc,
                trend="rising",
                detail="File count may increase without cleanup",
            ))

        return forecasts


MEMORY_TREND_THRESHOLD = 70.0  # %
