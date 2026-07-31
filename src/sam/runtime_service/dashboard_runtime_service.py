"""DashboardRuntimeService (Sprint 261).

Program D - Runtime Services & Deployment.
Service runtime khusus dashboard. Immutable, sync, deterministic.
"""
from __future__ import annotations
from typing import Optional

from .contract import RuntimeServiceContract
from .descriptor import RuntimeServiceDescriptor
from .metadata import RuntimeServiceMetadata
from .runtime_service import RuntimeService


class DashboardRuntimeService(RuntimeService):
    """Service runtime untuk dashboard."""

    def __init__(self, views: Optional[tuple] = None) -> None:
        descriptor = RuntimeServiceDescriptor(
            name="dashboard-runtime-service",
            service_type="runtime",
            description="Runtime service untuk dashboard (Program D).",
        )
        metadata = RuntimeServiceMetadata(
            service_id="dashboard-runtime-service",
            name="Dashboard Runtime Service",
            capabilities=["dashboard", "monitoring", "preview"],
        )
        contract = RuntimeServiceContract(
            service="dashboard-runtime-service",
            layers=["dashboard", "runtime-service"],
        )
        super().__init__(descriptor, metadata, contract)
        self._views = views or ("mission", "workflow", "execution", "approval")
