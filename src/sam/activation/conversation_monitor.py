"""Conversation Monitor Bridge — Sprint 86, 8 queries."""
from typing import Any, Dict, List, Optional
from sam.activation.activation_metrics import ActivationMetricsCollector, ActivationMetrics
from sam.activation.activation_monitor import ActivationMonitor, MonitorEvent
from sam.activation.activation_history import ActivationHistory, HistoryEntry
from sam.activation.activation_snapshot import ActivationSnapshotState
from sam.activation.activation_health import ActivationHealthChecker, ActivationHealthReport
from sam.activation.package_registry import PackageRegistry
from sam.activation.activation_package import ActivationPackage


class ConversationMonitor:
    """Conversation bridge untuk Monitoring — 8 queries."""

    def __init__(self, pkg_reg: PackageRegistry, monitor: ActivationMonitor,
                 history: ActivationHistory):
        self._pkg_reg = pkg_reg
        self._monitor = monitor
        self._history = history

    @property
    def query_count(self) -> int:
        return 8

    def query_metrics(self, collector: ActivationMetricsCollector) -> Dict[str, Any]:
        m = collector.collect(self._pkg_reg.list())
        return {
            "total_packages": m.total_packages,
            "total_candidates": m.total_candidates,
            "avg_confidence": m.avg_confidence,
            "avg_duration": m.avg_duration,
            "strategy_counts": m.strategy_counts,
        }

    def query_events(self, limit: int = 10) -> List[Dict[str, Any]]:
        return [
            {"event_id": e.event_id, "type": e.event_type,
             "package": e.package_ref, "timestamp": e.timestamp}
            for e in self._monitor.list_events(limit)
        ]

    def query_event_count(self) -> Dict[str, Any]:
        return {"total_events": self._monitor.count_events()}

    def query_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        return [
            {"entry_id": e.entry_id, "package_id": e.package_id,
             "action": e.action, "status": e.status}
            for e in self._history.list(limit)
        ]

    def query_history_count(self) -> Dict[str, Any]:
        return {"total_history": self._history.count()}

    def query_snapshot(self) -> Dict[str, Any]:
        packages = self._pkg_reg.list()
        collector = ActivationMetricsCollector()
        metrics = collector.collect(packages)
        snap = ActivationSnapshotState(
            snapshot_id="snap_main",
            total_packages=metrics.total_packages,
            total_events=self._monitor.count_events(),
            total_history=self._history.count(),
            status="active" if metrics.total_packages > 0 else "idle",
            metrics=metrics,
            recent_events=[e.event_id for e in self._monitor.list_events(5)],
        )
        return {
            "snapshot_id": snap.snapshot_id,
            "total_packages": snap.total_packages,
            "status": snap.status,
            "avg_confidence": metrics.avg_confidence,
        }

    def query_health(self) -> Dict[str, Any]:
        packages = self._pkg_reg.list()
        collector = ActivationMetricsCollector()
        metrics = collector.collect(packages)
        snap = ActivationSnapshotState(
            snapshot_id="health_check",
            total_packages=metrics.total_packages,
            total_events=self._monitor.count_events(),
            total_history=self._history.count(),
            metrics=metrics,
        )
        checker = ActivationHealthChecker()
        report = checker.check(snap)
        return {
            "healthy": report.healthy,
            "score": report.score,
            "issues": report.issues,
            "package_count": report.package_count,
        }

    def query_monitor_all(self, collector: ActivationMetricsCollector) -> Dict[str, Any]:
        metrics = collector.collect(self._pkg_reg.list())
        packages = self._pkg_reg.list()
        snap = ActivationSnapshotState(
            snapshot_id="monitor_all",
            total_packages=metrics.total_packages,
            total_events=self._monitor.count_events(),
            total_history=self._history.count(),
            metrics=metrics,
        )
        checker = ActivationHealthChecker()
        health = checker.check(snap)
        return {
            "packages": metrics.total_packages,
            "events": self._monitor.count_events(),
            "history": self._history.count(),
            "health_score": health.score,
            "healthy": health.healthy,
        }
