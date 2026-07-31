# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 129 - Coordination: conversation_coordination.

Read-only conversation bridge for coordination.
"""
from __future__ import annotations

from typing import Dict, Tuple

from .runtime_coordinator import RuntimeCoordinator
from .coordination_report import CoordinationReport


class ConversationCoordinationBridge:
    """Read-only bridge exposing coordination info."""

    def __init__(self, coordinator: RuntimeCoordinator) -> None:
        self._coordinator = coordinator

    def coordinate(self, chain: Tuple[str, ...]) -> CoordinationReport:
        return self._coordinator.coordinate(chain)

    def coordinated(self, report: CoordinationReport) -> int:
        return report.coordinated_count

    def summary(self) -> Dict[str, int]:
        return {"coordinated": len(self._coordinator._history)}
