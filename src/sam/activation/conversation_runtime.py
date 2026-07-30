"""Conversation Runtime Bridge — Sprint 87, 8 queries."""
from typing import Any, Dict, List, Optional
from sam.activation.activation_runtime import ActivationRuntimeEngine, RuntimeStatus
from sam.activation.activation_pipeline import ActivationPipeline
from sam.activation.activation_report import ActivationReport
from sam.activation.activation_runtime_report import RuntimeReport, RuntimeReportBuilder
from sam.activation.activation_runtime_status import ActivationRuntimeStatus, ActivationRuntimeStatusBuilder
from sam.activation.activation_metrics import ActivationMetricsCollector
from sam.activation.activation_snapshot import ActivationSnapshotState
from sam.activation.activation_health import ActivationHealthChecker
from sam.activation.activation_coordinator import ActivationCoordinator
from sam.activation.activation_context import ActivationContext
from sam.activation.activation_request import ActivationRequest


class ConversationRuntime:
    """Conversation bridge untuk Runtime — 8 queries."""

    def __init__(self, coordinator: ActivationCoordinator):
        self._coord = coordinator

    @property
    def query_count(self) -> int:
        return 8

    def query_status(self) -> Dict[str, Any]:
        s = self._coord.engine.status()
        return {
            "running": s.pipeline_running,
            "phase": s.current_phase,
            "packages": s.total_packages,
            "status": s.status,
        }

    def query_pipeline_phases(self) -> List[str]:
        return list(ActivationPipeline.PIPELINE_PHASES)

    def query_run_pipeline(self, ctx: ActivationContext,
                            req: ActivationRequest) -> Dict[str, Any]:
        pkg = self._coord.pipeline.run(ctx, req)
        return {
            "package_id": pkg.package_id,
            "strategy": pkg.strategy_ref,
            "candidates": pkg.total_candidates,
            "status": pkg.status,
        }

    def query_report(self) -> Dict[str, Any]:
        pkgs = self._coord.engine.list_packages()
        metrics = ActivationMetricsCollector().collect(pkgs)
        snap = ActivationSnapshotState(
            "rt_report", len(pkgs), self._coord.monitor.count_events(),
            self._coord.history.count(), metrics=metrics,
        )
        health = ActivationHealthChecker().check(snap)
        status = self._coord.engine.status()
        builder = RuntimeReportBuilder()
        report = builder.build("rt_report", status, metrics, health,
                               ActivationPipeline.PIPELINE_PHASES)
        return {
            "report_id": report.report_id,
            "ready": report.ready_for_execution,
            "health_score": report.health_score,
            "packages": report.total_packages,
            "summary": report.summary,
        }

    def query_full_status(self) -> Dict[str, Any]:
        pkgs = self._coord.engine.list_packages()
        metrics = ActivationMetricsCollector().collect(pkgs)
        snap = ActivationSnapshotState(
            "rt_full", len(pkgs), self._coord.monitor.count_events(),
            self._coord.history.count(), metrics=metrics,
        )
        health = ActivationHealthChecker().check(snap)
        status = self._coord.engine.status()
        sb = ActivationRuntimeStatusBuilder()
        rt = sb.build(status, health, self._coord.engine._phase)
        return {
            "overall": rt.overall_status,
            "ready": rt.ready,
            "health": rt.health,
            "packages": rt.package_count,
            "issues": rt.issues,
        }

    def query_engine_packages(self) -> List[Dict[str, Any]]:
        return [
            {"package_id": p.package_id, "strategy": p.strategy_ref,
             "candidates": p.total_candidates, "confidence": p.confidence}
            for p in self._coord.engine.list_packages()
        ]

    def query_complete(self) -> Dict[str, Any]:
        self._coord.engine.complete()
        return {"status": "complete", "phase": "complete"}

    def query_advance_phase(self, phase: str) -> Dict[str, Any]:
        self._coord.engine.advance_phase(phase)
        return {"phase": phase, "running": self._coord.engine.status().pipeline_running}
