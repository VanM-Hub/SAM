"""Orchestrator — orchestrator task."""
from __future__ import annotations
from typing import Dict, List
from sam.runtime_kernel.runtime_coordinator import OrchestrationOrder, CoordinationResult


class Orchestrator:
    """Orchestrator task — preview-only."""

    def __init__(self) -> None:
        self._orders: Dict[str, OrchestrationOrder] = {}

    def add(self, order: OrchestrationOrder) -> None:
        self._orders[order.order_id] = order

    def get(self, order_id: str) -> OrchestrationOrder | None:
        return self._orders.get(order_id)

    def execute(self, order_id: str) -> CoordinationResult:
        order = self._orders.get(order_id)
        if not order:
            return CoordinationResult(order_id, False, "order not found")
        return CoordinationResult(order_id, True, f"{order.subsystem}: {order.command}")

    def count(self) -> int:
        return len(self._orders)

    def list_pending(self) -> List[OrchestrationOrder]:
        return list(self._orders.values())
