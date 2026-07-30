"""Dashboard Monitor Bridge — Sprint 86, 5 cards."""
from typing import Any, Dict, List
from dataclasses import dataclass, field
from sam.activation.package_registry import PackageRegistry
from sam.activation.activation_monitor import ActivationMonitor
from sam.activation.activation_history import ActivationHistory
from sam.activation.activation_metrics import ActivationMetricsCollector
from sam.activation.activation_snapshot import ActivationSnapshotState
from sam.activation.activation_health import ActivationHealthChecker


@dataclass(frozen=True)
class MonitorCard:
    card_type: str = ""
    title: str = ""
    items: List[str] = field(default_factory=list)


class DashboardMonitor:
    """Dashboard bridge untuk Monitoring — 5 cards."""

    def __init__(self, pkg_reg: PackageRegistry, monitor: ActivationMonitor,
                 history: ActivationHistory):
        self._pkg_reg = pkg_reg
        self._monitor = monitor
        self._history = history

    @property
    def card_count(self) -> int:
        return 5

    def get_cards(self) -> List[MonitorCard]:
        return [
            self._metrics_card(),
            self._events_card(),
            self._history_card(),
            self._snapshot_card(),
            self._health_card(),
        ]

    def _metrics_card(self) -> MonitorCard:
        collector = ActivationMetricsCollector()
        m = collector.collect(self._pkg_reg.list())
        return MonitorCard(
            "metrics", "Activation Metrics",
            [f"Packages: {m.total_packages}", f"Candidates: {m.total_candidates}",
             f"Avg Confidence: {m.avg_confidence}", f"Avg Duration: {m.avg_duration}s"],
        )

    def _events_card(self) -> MonitorCard:
        events = self._monitor.list_events(5)
        return MonitorCard(
            "events", "Recent Events",
            [f"{e.event_id}: {e.event_type} ({e.package_ref})" for e in events] or ["No events"],
        )

    def _history_card(self) -> MonitorCard:
        entries = self._history.list(5)
        return MonitorCard(
            "history", "Recent History",
            [f"{e.entry_id}: {e.action} -> {e.package_id} ({e.status})" for e in entries] or ["No history"],
        )

    def _snapshot_card(self) -> MonitorCard:
        packages = self._pkg_reg.list()
        collector = ActivationMetricsCollector()
        metrics = collector.collect(packages)
        snap = ActivationSnapshotState(
            snapshot_id="dash_snap",
            total_packages=metrics.total_packages,
            total_events=self._monitor.count_events(),
            total_history=self._history.count(),
            status="active" if metrics.total_packages > 0 else "idle",
            metrics=metrics,
        )
        return MonitorCard(
            "snapshot", "Activation Snapshot",
            [f"Status: {snap.status}", f"Packages: {snap.total_packages}",
             f"Events: {snap.total_events}", f"History: {snap.total_history}"],
        )

    def _health_card(self) -> MonitorCard:
        collector = ActivationMetricsCollector()
        metrics = collector.collect(self._pkg_reg.list())
        snap = ActivationSnapshotState(
            snapshot_id="dash_health", total_packages=metrics.total_packages,
            total_events=self._monitor.count_events(),
            total_history=self._history.count(), metrics=metrics,
        )
        checker = ActivationHealthChecker()
        report = checker.check(snap)
        return MonitorCard(
            "health", "Activation Health",
            [f"Healthy: {'✅' if report.healthy else '❌'}",
             f"Score: {report.score}",
             f"Issues: {', '.join(report.issues) if report.issues else 'None'}",
             f"Packages: {report.package_count}"],
        )
