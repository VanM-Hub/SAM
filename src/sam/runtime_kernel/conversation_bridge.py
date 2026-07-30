"""Conversation Bridge / Adapter — 8 queries."""
from __future__ import annotations
from typing import List
from sam.runtime_kernel.adapter_registry import AdapterRegistry
from sam.runtime_kernel.bridge_router import BridgeRouter
from sam.runtime_kernel.transform_engine import TransformEngine
from sam.runtime_kernel.protocol_mapper import ProtocolMapper


class ConversationBridge:
    def __init__(self, registry: AdapterRegistry, router: BridgeRouter,
                 transform: TransformEngine, mapper: ProtocolMapper) -> None:
        self._registry = registry
        self._router = router
        self._transform = transform
        self._mapper = mapper

    def get_adapter_registry(self) -> AdapterRegistry:
        return self._registry

    def get_bridge_router(self) -> BridgeRouter:
        return self._router

    def get_transform_engine(self) -> TransformEngine:
        return self._transform

    def get_protocol_mapper(self) -> ProtocolMapper:
        return self._mapper

    def describe_layers(self) -> List[str]:
        return ["adapter", "router", "transform", "protocol"]

    def count_layers(self) -> int:
        return 4

    def get_registered_subsystems(self) -> List[str]:
        names = {a.subsystem_name for a in self._registry.list_all()}
        return list(names) if names else ["none"]

    def count_adapters(self) -> int:
        return self._registry.count()


class DashboardBridge:
    def __init__(self, registry: AdapterRegistry, router: BridgeRouter,
                 transform: TransformEngine, mapper: ProtocolMapper) -> None:
        self._registry = registry
        self._router = router
        self._transform = transform
        self._mapper = mapper

    def engine_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Bridge Engine",
            description=f"{self._registry.count()} adapters",
            status="ready",
            metrics={"adapters": self._registry.count(),
                     "routes": self._router.count(),
                     "rules": self._transform.count(),
                     "protocols": self._mapper.count()},
            items=["adapter", "router", "transform", "protocol"],
        )

    def adapter_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Adapter Registry",
            description=f"{self._registry.count()} adapters",
            status="ready",
            metrics={"count": self._registry.count()},
            items=["adapters"],
        )

    def router_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Bridge Router",
            description=f"{self._router.count()} routes",
            status="ready",
            metrics={"routes": self._router.count(),
                     "active": len(self._router.list_active())},
            items=["routes"],
        )

    def transform_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Transform Engine",
            description=f"{self._transform.count()} rules",
            status="ready",
            metrics={"rules": self._transform.count()},
            items=["transforms"],
        )

    def summary_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Bridge Summary",
            description="Ringkasan bridge runtime",
            status="ready",
            metrics={"layers": 4, "adapters": self._registry.count()},
            items=["adapter", "router", "transform", "protocol"],
        )
