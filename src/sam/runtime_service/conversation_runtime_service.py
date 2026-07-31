"""ConversationRuntimeService (Sprint 261).

Program D - Runtime Services & Deployment.
Service runtime khusus percakapan. Immutable, sync, deterministic.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from .contract import RuntimeServiceContract
from .descriptor import RuntimeServiceDescriptor
from .metadata import RuntimeServiceMetadata
from .runtime_service import RuntimeService


@dataclass(frozen=True)
class ConversationRuntimeServiceDescriptor(RuntimeServiceDescriptor):
    """Descriptor service percakapan."""
    service_type: str = "runtime"
    channels: tuple = ("conversation",)


class ConversationRuntimeService(RuntimeService):
    """Service runtime untuk percakapan."""

    def __init__(self, channels: Optional[tuple] = None) -> None:
        descriptor = RuntimeServiceDescriptor(
            name="conversation-runtime-service",
            service_type="runtime",
            description="Runtime service untuk percakapan (Program D).",
        )
        metadata = RuntimeServiceMetadata(
            service_id="conversation-runtime-service",
            name="Conversation Runtime Service",
            capabilities=["conversation", "preview", "execute"],
        )
        contract = RuntimeServiceContract(
            service="conversation-runtime-service",
            layers=["conversation", "runtime-service"],
        )
        super().__init__(descriptor, metadata, contract)
        self._channels = channels or ("conversation",)
