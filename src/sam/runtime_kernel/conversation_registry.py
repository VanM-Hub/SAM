"""Conversation Registry Bridge — 8 queries."""
from __future__ import annotations
from typing import List
from sam.runtime_kernel.runtime_catalog import RuntimeCatalog
from sam.runtime_kernel.runtime_locator import RuntimeLocator
from sam.runtime_kernel.runtime_descriptor import DescriptorEngine
from sam.runtime_kernel.runtime_manifest import ManifestEngine


class ConversationRegistry:
    """Conversation bridge untuk registry — 8 queries."""

    def __init__(self, catalog: RuntimeCatalog, locator: RuntimeLocator,
                 desc: DescriptorEngine, manifest: ManifestEngine) -> None:
        self._catalog = catalog
        self._locator = locator
        self._desc = desc
        self._manifest = manifest

    def get_catalog(self) -> RuntimeCatalog:
        return self._catalog

    def get_locator(self) -> RuntimeLocator:
        return self._locator

    def get_descriptor_engine(self) -> DescriptorEngine:
        return self._desc

    def get_manifest_engine(self) -> ManifestEngine:
        return self._manifest

    def describe_components(self) -> List[str]:
        return ["catalog", "locator", "descriptor", "manifest"]

    def count_components(self) -> int:
        return 4

    def get_registered_subsystems(self) -> List[str]:
        return ["guardian", "decision", "approval", "activation", "execution", "kernel"]

    def count_subsystems(self) -> int:
        return 6


class DashboardRegistry:
    """Dashboard bridge untuk registry — 5 cards."""

    def __init__(self, catalog: RuntimeCatalog) -> None:
        self._catalog = catalog

    def engine_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Runtime Registry",
            description=f"{self._catalog.count_entries()} entries",
            status="ready",
            metrics={"components": 4, "subsystems": 6},
            items=["catalog", "locator", "descriptor", "manifest"],
        )

    def catalog_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Runtime Catalog",
            description="Katalog subsystem",
            status="ready",
            metrics={"entries": self._catalog.count_entries()},
            items=["categories"],
        )

    def descriptor_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Runtime Descriptors",
            description="Deskripsi subsystem",
            status="ready",
            metrics={"descriptors": 0},
            items=["capabilities"],
        )

    def manifest_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Runtime Manifests",
            description="Manifest subsystem",
            status="ready",
            metrics={"manifests": 0},
            items=["dependencies"],
        )

    def summary_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Registry Summary",
            description="Ringkasan registri runtime",
            status="ready",
            metrics={"entries": self._catalog.count_entries()},
            items=["catalog", "descriptor", "manifest", "locator"],
        )
