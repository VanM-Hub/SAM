"""Dashboard Runtime Bridge — Sprint 87, 5 cards."""
from typing import Any, Dict, List
from dataclasses import dataclass, field
from sam.activation.activation_pipeline import ActivationPipeline
from sam.activation.activation_metrics import ActivationMetricsCollector
from sam.activation.activation_snapshot import ActivationSnapshotState
from sam.activation.activation_health import ActivationHealthChecker
from sam.activation.activation_runtime_report import RuntimeReportBuilder
from sam.activation.activation_runtime_status import ActivationRuntimeStatusBuilder


@dataclass(frozen=True)
class RuntimeCard:
    card_type: str = ""
    title: str = ""
    items: List[str] = field(default_factory=list)


class DashboardRuntime:
    """Dashboard bridge untuk Runtime — 5 cards."""

    def __init__(self, coordinator: Any):
        self._coord = coordinator

    @property
    def card_count(self) -> int:
        return 5

    def get_cards(self) -> List[RuntimeCard]:
        return [
            self._status_card(),
            self._pipeline_card(),
            self._report_card(),
            self._packages_card(),
            self._summary_card(),
        ]

    def _status_card(self) -> RuntimeCard:
        s = self._coord.engine.status()
        return RuntimeCard(
            "status", "Runtime Status",
            [f"Running: {s.pipeline_running}", f"Phase: {s.current_phase}",
             f"Status: {s.status}", f"Packages: {s.total_packages}"],
        )

    def _pipeline_card(self) -> RuntimeCard:
        phases = ActivationPipeline.PIPELINE_PHASES
        return RuntimeCard(
            "pipeline", "Pipeline Phases",
            [f"Total phases: {len(phases)}"] + [f"  - {p}" for p in phases],
        )

    def _report_card(self) -> RuntimeCard:
        pkgs = self._coord.engine.list_packages()
        metrics = ActivationMetricsCollector().collect(pkgs)
        snap = ActivationSnapshotState(
            "dash_report", len(pkgs), self._coord.monitor.count_events(),
            self._coord.history.count(), metrics=metrics,
        )
        health = ActivationHealthChecker().check(snap)
        status = self._coord.engine.status()
        builder = RuntimeReportBuilder()
        report = builder.build("dash_report", status, metrics, health,
                               ActivationPipeline.PIPELINE_PHASES)
        return RuntimeCard(
            "report", "Runtime Report",
            [f"Ready: {'✅' if report.ready_for_execution else '❌'}",
             f"Health: {report.health_score:.2f}",
             f"Packages: {report.total_packages}", report.summary],
        )

    def _packages_card(self) -> RuntimeCard:
        pkgs = self._coord.engine.list_packages()
        return RuntimeCard(
            "packages", "Activation Packages",
            [f"{p.package_id}: {p.total_candidates} candidates, conf={p.confidence}, {p.strategy_ref}"
             for p in pkgs] or ["No packages"],
        )

    def _summary_card(self) -> RuntimeCard:
        pkgs = self._coord.engine.list_packages()
        metrics = ActivationMetricsCollector().collect(pkgs)
        snap = ActivationSnapshotState(
            "dash_summary", len(pkgs), self._coord.monitor.count_events(),
            self._coord.history.count(), metrics=metrics,
        )
        health = ActivationHealthChecker().check(snap)
        status = self._coord.engine.status()
        sb = ActivationRuntimeStatusBuilder()
        rt = sb.build(status, health, self._coord.engine._phase)
        return RuntimeCard(
            "summary", "Activation Summary",
            [f"Overall: {rt.overall_status}",
             f"Ready: {'✅' if rt.ready else '❌'}",
             f"Health: {rt.health:.2f}",
             f"Issues: {', '.join(rt.issues) if rt.issues else 'None'}"],
        )
