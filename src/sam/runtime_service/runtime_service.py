"""RuntimeService (Sprint 261).

Program D - Runtime Services & Deployment.
Entry-point base untuk service runtime. Immutable, sync, deterministic.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict

from .contract import RuntimeServiceContract
from .descriptor import RuntimeServiceDescriptor
from .metadata import RuntimeServiceMetadata


@dataclass(frozen=True)
class RuntimeServiceState:
    """State service (immutable)."""
    name: str
    status: str = "created"  # created|initializing|ready|running|stopping|stopped|failed
    initialized: bool = False
    started: bool = False


class RuntimeService:
    """Service runtime — base class untuk semua service Program D."""

    def __init__(self, descriptor: RuntimeServiceDescriptor,
                 metadata: RuntimeServiceMetadata,
                 contract: RuntimeServiceContract) -> None:
        self._descriptor = descriptor
        self._metadata = metadata
        self._contract = contract
        self._state = RuntimeServiceState(name=descriptor.name)
        self._initialized = False

    @property
    def name(self) -> str:
        return self._descriptor.name

    @property
    def descriptor(self) -> RuntimeServiceDescriptor:
        return self._descriptor

    @property
    def metadata(self) -> RuntimeServiceMetadata:
        return self._metadata

    @property
    def contract(self) -> RuntimeServiceContract:
        return self._contract

    @property
    def status(self) -> str:
        return self._state.status

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    def initialize(self) -> None:
        if self._initialized:
            return
        if not self._contract.validate():
            raise RuntimeError(f"contract invalid for service: {self.name}")
        self._initialized = True
        self._state = RuntimeServiceState(
            name=self.name, status="initializing", initialized=True
        )
        self._state = RuntimeServiceState(
            name=self.name, status="ready", initialized=True
        )

    def status_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self._state.status,
            "initialized": self._state.initialized,
            "started": self._state.started,
        }
