"""Activation Pipeline — pipeline aktivasi lengkap."""
from typing import Any, Dict, List, Optional
from sam.activation.activation_context import ActivationContext
from sam.activation.activation_request import ActivationRequest
from sam.activation.activation_draft import ActivationDraft
from sam.activation.activation_package import ActivationPackage
from sam.activation.activation_sequence import ActivationSequence
from sam.activation.activation_strategy import ActivationStrategy
from sam.activation.activation_report import ActivationReport
from sam.activation.activation_runtime import ActivationRuntimeEngine
from sam.activation.activation_registry import ActivationRegistry
from sam.activation.activation_builder import ActivationBuilder
from sam.activation.activation_validator import ActivationValidator
from sam.activation.activation_constraints import ActivationConstraints
from sam.activation.activation_readiness import ActivationReadiness
from sam.activation.activation_priority import ActivationPriority
from sam.activation.activation_window import ActivationWindowManager
from sam.activation.package_builder import PackageBuilder
from sam.activation.package_registry import PackageRegistry
from sam.activation.activation_monitor import ActivationMonitor
from sam.activation.activation_history import ActivationHistory
from sam.activation.activation_metrics import ActivationMetricsCollector
from sam.activation.activation_report import ActivationReportBuilder
from sam.activation.activation_health import ActivationHealthChecker


class ActivationPipeline:
    """Pipeline aktivasi lengkap — orchestrator semua fase."""

    PIPELINE_PHASES = [
        "context", "build", "validate", "constrain",
        "strategy", "package", "monitor", "complete",
    ]

    def __init__(self):
        self._registry = ActivationRegistry()
        self._pkg_registry = PackageRegistry()
        self._engine = ActivationRuntimeEngine()
        self._monitor = ActivationMonitor()
        self._history = ActivationHistory()
        self._builder = ActivationBuilder()
        self._validator = ActivationValidator()
        self._constraints = ActivationConstraints()
        self._readiness = ActivationReadiness()
        self._priority = ActivationPriority()
        self._window_mgr = ActivationWindowManager()
        self._pkg_builder = PackageBuilder()
        self._report_builder = ActivationReportBuilder()
        self._metrics_collector = ActivationMetricsCollector()
        self._health_checker = ActivationHealthChecker()

    @property
    def registry(self) -> ActivationRegistry:
        return self._registry

    @property
    def engine(self) -> ActivationRuntimeEngine:
        return self._engine

    @property
    def monitor(self) -> ActivationMonitor:
        return self._monitor

    @property
    def history(self) -> ActivationHistory:
        return self._history

    def run(self, ctx: ActivationContext, req: ActivationRequest,
            timestamp: float = 0.0) -> ActivationPackage:
        """Pipeline lengkap: context → package."""
        self._engine.start(timestamp)

        # 1. Context
        self._registry.register_context(ctx)
        self._registry.register_request(req)

        # 2. Build
        candidates = self._builder.build(ctx, req)
        for c in candidates:
            self._registry.register_candidate(c)
        draft = ActivationDraft(
            draft_id=f"draft_{ctx.context_id}",
            context_id=ctx.context_id,
            candidates=len(candidates),
            top_candidate=candidates[0].candidate_id if candidates else "",
        )

        # 3. Strategy
        conf_avg = sum(c.confidence for c in candidates) / len(candidates) if candidates else 0.0
        from sam.activation.activation_strategy import ActivationStrategyEngine
        strat_engine = ActivationStrategyEngine()
        strategy = strat_engine.select(ctx.environment, len(candidates), conf_avg)

        # 4. Sequence
        from sam.activation.activation_sequence import SequenceBuilder
        seq_builder = SequenceBuilder()
        assign = self._priority.assign(candidates)
        sequence = seq_builder.build(strategy, assign, candidates)

        # 5. Package
        pkg = self._pkg_builder.build(sequence, strategy, req.plan_id)

        # 6. Register + monitor
        self._pkg_registry.register(pkg)
        self._engine.register_package(pkg)
        self._monitor.record("built", pkg, timestamp)
        self._history.record(pkg, "pipeline_complete", timestamp)
        self._engine.advance_phase("packaged")

        return pkg
