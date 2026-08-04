"""Runtime Service (Program D - Runtime Services & Deployment).

Sprints 261-271, v27.0.0.
Entry point resmi untuk menjalankan SAM sebagai service nyata.
Immutable, sync, deterministic. Tidak melakukan network call.

Session 01 (Foundation Activation): ekspos WebRuntimeService sebagai API
publik agar Web menjadi consumer produksi pertama RuntimeService.
WebRuntimeService = gateway kontrak & lifecycle (bukan executor).
"""
from __future__ import annotations

from .runtime_service import RuntimeService, RuntimeServiceState
from .contract import RuntimeServiceContract
from .descriptor import RuntimeServiceDescriptor
from .metadata import RuntimeServiceMetadata
from .web_runtime_service import WebRuntimeService, WebRuntimeServiceDescriptor
from .runtime_registry import RuntimeRegistry
from .service_registry import RuntimeServiceRegistry, RegisteredService

RUNTIME_SERVICE_VERSION = "27.0.0"

__all__ = [
    "RUNTIME_SERVICE_VERSION",
    "RuntimeService",
    "RuntimeServiceState",
    "RuntimeServiceContract",
    "RuntimeServiceDescriptor",
    "RuntimeServiceMetadata",
    "WebRuntimeService",
    "WebRuntimeServiceDescriptor",
    "RuntimeRegistry",
    "RuntimeServiceRegistry",
    "RegisteredService",
]
