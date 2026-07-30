"""Activation Coordinator — koordinator semua komponen runtime."""
from typing import Any, Dict, List, Optional
from sam.activation.activation_runtime import ActivationRuntimeEngine
from sam.activation.activation_pipeline import ActivationPipeline
from sam.activation.activation_context import ActivationContext
from sam.activation.activation_request import ActivationRequest
from sam.activation.activation_package import ActivationPackage
from sam.activation.activation_monitor import ActivationMonitor
from sam.activation.activation_history import ActivationHistory
from sam.activation.activation_metrics import ActivationMetricsCollector
from sam.activation.activation_snapshot import ActivationSnapshotState
from sam.activation.activation_health import ActivationHealthChecker
from sam.activation.conversation_activation import ConversationActivation
from sam.activation.conversation_validation import ConversationValidation
from sam.activation.conversation_strategy import ConversationStrategy
from sam.activation.conversation_package import ConversationPackage
from sam.activation.conversation_monitor import ConversationMonitor
from sam.activation.dashboard_activation import DashboardActivation
from sam.activation.dashboard_validation import DashboardValidation
from sam.activation.dashboard_strategy import DashboardStrategy
from sam.activation.dashboard_package import DashboardPackage
from sam.activation.dashboard_monitor import DashboardMonitor
from sam.activation.dashboard_runtime import DashboardRuntime
from sam.activation.package_registry import PackageRegistry


class ActivationCoordinator:
    """Koordinator akses ke semua komponen Activation Runtime."""

    def __init__(self, pipeline: ActivationPipeline):
        self._pipeline = pipeline

    @property
    def pipeline(self) -> ActivationPipeline:
        return self._pipeline

    @property
    def engine(self) -> ActivationRuntimeEngine:
        return self._pipeline.engine

    @property
    def monitor(self) -> ActivationMonitor:
        return self._pipeline.monitor

    @property
    def history(self) -> ActivationHistory:
        return self._pipeline.history

    @property
    def conversation_activation(self) -> ConversationActivation:
        return ConversationActivation(self._pipeline.registry)

    @property
    def conversation_validation(self) -> ConversationValidation:
        return ConversationValidation(self._pipeline.registry)

    @property
    def conversation_strategy(self) -> ConversationStrategy:
        return ConversationStrategy(self._pipeline.registry)

    @property
    def conversation_package(self) -> ConversationPackage:
        return ConversationPackage(self._pipeline._pkg_registry)

    @property
    def conversation_monitor(self) -> ConversationMonitor:
        return ConversationMonitor(
            self._pipeline._pkg_registry,
            self._pipeline.monitor,
            self._pipeline.history,
        )

    @property
    def dashboard_activation(self) -> DashboardActivation:
        return DashboardActivation(self._pipeline.registry)

    @property
    def dashboard_validation(self) -> DashboardValidation:
        return DashboardValidation(self._pipeline.registry)

    @property
    def dashboard_strategy(self) -> DashboardStrategy:
        return DashboardStrategy(self._pipeline.registry)

    @property
    def dashboard_package(self) -> DashboardPackage:
        return DashboardPackage(self._pipeline._pkg_registry)

    @property
    def dashboard_monitor(self) -> DashboardMonitor:
        return DashboardMonitor(
            self._pipeline._pkg_registry,
            self._pipeline.monitor,
            self._pipeline.history,
        )

    @property
    def dashboard_runtime(self) -> DashboardRuntime:
        return DashboardRuntime(self)
