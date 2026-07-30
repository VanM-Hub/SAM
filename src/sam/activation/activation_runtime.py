"""Activation Runtime Engine — aktivasi pipeline final."""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from sam.activation.activation_context import ActivationContext
from sam.activation.activation_request import ActivationRequest
from sam.activation.activation_draft import ActivationDraft
from sam.activation.activation_package import ActivationPackage
from sam.activation.activation_sequence import ActivationSequence
from sam.activation.activation_strategy import ActivationStrategy
from sam.activation.activation_report import ActivationReport
from sam.activation.activation_metrics import ActivationMetrics
from sam.activation.activation_snapshot import ActivationSnapshotState


@dataclass(frozen=True)
class RuntimeStatus:
    pipeline_running: bool = False
    current_phase: str = "idle"
    total_packages: int = 0
    last_updated: float = 0.0
    status: str = "idle"


class ActivationRuntimeEngine:
    """Engine utama aktivasi — orchestrator pipeline."""

    def __init__(self):
        self._running = False
        self._phase = "idle"
        self._packages: List[ActivationPackage] = []
        self._last_updated = 0.0

    def start(self, timestamp: float = 0.0) -> RuntimeStatus:
        self._running = True
        self._phase = "building"
        self._last_updated = timestamp
        return self.status()

    def status(self) -> RuntimeStatus:
        return RuntimeStatus(
            pipeline_running=self._running,
            current_phase=self._phase,
            total_packages=len(self._packages),
            last_updated=self._last_updated,
            status="running" if self._running else "idle",
        )

    def register_package(self, pkg: ActivationPackage) -> None:
        self._packages.append(pkg)
        self._phase = "packaged"

    def advance_phase(self, phase: str) -> None:
        self._phase = phase

    def complete(self) -> None:
        self._running = False
        self._phase = "complete"

    def list_packages(self) -> List[ActivationPackage]:
        return list(self._packages)
