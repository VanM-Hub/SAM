"""WebRuntimeService (Session 01 - Foundation Activation).

Program D - Runtime Services & Deployment.
Service runtime khusus Web (Runtime/Lifecycle/Status endpoint).

GATEWAY KONTRAK & LIFECYCLE — BUKAN executor/coordinator/dispatcher.
- Tidak membuat keputusan.
- Tidak melakukan orchestration.
- Tidak mengetahui provider / approval / execution nyata.
- Lifecycle: created -> initializing -> ready (initialize()).
- status_dict() menyajikan status lifecycle service.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from .contract import RuntimeServiceContract
from .descriptor import RuntimeServiceDescriptor
from .metadata import RuntimeServiceMetadata
from .runtime_service import RuntimeService


@dataclass(frozen=True)
class WebRuntimeServiceDescriptor(RuntimeServiceDescriptor):
    """Descriptor service web (Runtime/Lifecycle/Status)."""
    service_type: str = "runtime"
    views: tuple = ("runtime", "lifecycle", "status")


class WebRuntimeService(RuntimeService):
    """Runtime service untuk Web (Runtime/Lifecycle/Status). Consumer pertama Program D."""

    def __init__(self, views: Optional[tuple] = None) -> None:
        descriptor = RuntimeServiceDescriptor(
            name="web-runtime-service",
            service_type="runtime",
            description="Runtime service untuk Web Runtime/Lifecycle/Status endpoint (Session 01).",
            tags=["web", "runtime", "lifecycle", "status"],
        )
        metadata = RuntimeServiceMetadata(
            service_id="web-runtime-service",
            name="Web Runtime Service",
            capabilities=["web", "runtime", "lifecycle", "status"],
        )
        contract = RuntimeServiceContract(
            service="web-runtime-service",
            layers=["web", "runtime-service"],
        )
        super().__init__(descriptor, metadata, contract)
        self._views = views or ("runtime", "lifecycle", "status")
