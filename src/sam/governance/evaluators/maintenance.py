"""
Maintenance Evaluator – Sprint 21 Fase 2

Checks whether the cluster is currently inside a maintenance window.
If so, the graph must WAIT.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional, List, Dict, Any

from ..evaluator import BaseEvaluator
from ..models import GovernanceDecision, GovernanceResult

if TYPE_CHECKING:
    from ...execution.graph import ExecutionGraph
    from ...runtime.context import ExecutionContext


class MaintenanceEvaluator(BaseEvaluator):
    """Evaluates whether execution falls within a maintenance window.

    Maintenance windows can come from:
    - Graph metadata (``maintenance_ends_at`` ISO timestamp)
    - A ``get_maintenance_windows()`` callable injected at construction
      (returns list of dicts with ``start``, ``end``, ``reason``)
    - Fallback: cluster-level maintenance flag via ``is_maintenance_active()`` callable

    If inside an active window → WAIT with suggested_delay until window ends.
    """

    def __init__(
        self,
        *,
        now_fn: callable = None,
        maintenance_windows: Optional[callable] = None,
        is_maintenance_active: Optional[callable] = None,
    ) -> None:
        super().__init__()
        self._now_fn = now_fn or datetime.utcnow
        self._maintenance_windows = maintenance_windows
        self._is_maintenance_active = is_maintenance_active

    @property
    def name(self) -> str:
        return "maintenance"

    async def _do_evaluate(
        self,
        graph: "ExecutionGraph",
        context: "ExecutionContext",
    ) -> GovernanceResult:
        return self._evaluate_sync(graph)

    def _evaluate_sync(self, graph: "ExecutionGraph") -> GovernanceResult:
        now = self._now_fn()
        metadata = getattr(graph, "metadata", {}) or {}

        # 1. Check graph-level maintenance window
        maintenance_ends_at = metadata.get("maintenance_ends_at")
        if maintenance_ends_at:
            try:
                end_dt = datetime.fromisoformat(str(maintenance_ends_at))
                if now < end_dt:
                    delay = int((end_dt - now).total_seconds())
                    return GovernanceResult.wait(
                        reason=f"Maintenance window active until {maintenance_ends_at}",
                        suggested_delay=max(0, delay),
                        metadata={"maintenance_ends_at": maintenance_ends_at},
                    )
            except (ValueError, TypeError):
                self._logger.warning(
                    "invalid_maintenance_ends_at",
                    value=maintenance_ends_at,
                )

        # 2. Check cluster-level maintenance windows
        if self._maintenance_windows:
            windows: List[Dict[str, Any]] = self._maintenance_windows()
            for win in windows:
                start = win.get("start")
                end = win.get("end")
                if start and end:
                    try:
                        start_dt = datetime.fromisoformat(str(start))
                        end_dt = datetime.fromisoformat(str(end))
                        if start_dt <= now < end_dt:
                            delay = int((end_dt - now).total_seconds())
                            return GovernanceResult.wait(
                                reason=f"Cluster maintenance: {win.get('reason', 'unknown')}",
                                suggested_delay=max(0, delay),
                                metadata={"maintenance_window": win},
                            )
                    except (ValueError, TypeError):
                        continue

        # 3. Check maintenance flag (fallback)
        if self._is_maintenance_active and self._is_maintenance_active():
            return GovernanceResult.wait(
                reason="Maintenance mode is active",
                suggested_delay=600,  # default 10 minutes
            )

        return GovernanceResult.allowed(reason="No active maintenance window")
