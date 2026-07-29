# OP-441 — Execution Provider Protocol
# Python 3.8, frozen DTO, synchronous, preview only

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple, Protocol
import uuid

from sam.execution.adapters.execution_envelope import ExecutionEnvelope, ExecutionEnvelopeItem


@dataclass(frozen=True)
class ProviderStatus:
    value: str = "idle"

    @staticmethod
    def idle(): return ProviderStatus("idle")
    @staticmethod
    def ready(): return ProviderStatus("ready")
    @staticmethod
    def processing(): return ProviderStatus("processing")
    @staticmethod
    def completed(): return ProviderStatus("completed")
    @staticmethod
    def failed(): return ProviderStatus("failed")
    @staticmethod
    def unavailable(): return ProviderStatus("unavailable")
    def is_terminal(self): return self.value in ("completed","failed","unavailable")


@dataclass(frozen=True)
class ProviderCapability:
    name: str = ""
    description: str = ""
    actions: Tuple[str, ...] = field(default_factory=tuple)
    provider_type: str = ""
    requires_approval: bool = True
    risk_level: str = "low"
    supports_preview: bool = True


@dataclass(frozen=True)
class ProviderMetadata:
    provider_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    provider_type: str = ""
    name: str = ""
    version: str = "1.0.0"
    description: str = ""
    capabilities: Tuple[ProviderCapability, ...] = field(default_factory=tuple)
    healthy: bool = True
    status: ProviderStatus = field(default_factory=ProviderStatus.idle)


@dataclass(frozen=True)
class ProviderDescriptor:
    provider_id: str = ""
    provider_type: str = ""
    name: str = ""
    version: str = ""
    healthy: bool = True
    capability_names: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ProviderRequest:
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    envelope: Optional[ExecutionEnvelope] = None
    provider_type: str = ""
    action: str = ""
    target: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProviderResponse:
    response_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    success: bool = False
    preview: str = ""
    estimated_duration: int = 0
    affected_resources: Tuple[str, ...] = field(default_factory=tuple)
    rollback_available: bool = True
    error: str = ""
    provider_type: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ExecutionProviderProtocol(Protocol):
    @property
    def metadata(self) -> ProviderMetadata: ...
    def execute_preview(self, request: ProviderRequest) -> ProviderResponse: ...
    def supported_actions(self) -> Tuple[str, ...]: ...
    def health(self) -> ProviderMetadata: ...


class BaseProvider:
    def __init__(self, provider_type: str, name: str, version: str = "1.0.0",
                 description: str = ""):
        self._provider_id = str(uuid.uuid4())
        self._provider_type = provider_type; self._name = name
        self._version = version; self._description = description
        self._capabilities: List[ProviderCapability] = []
        self._healthy = True
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(provider_id=self._provider_id, provider_type=self._provider_type,
            name=self._name, version=self._version, description=self._description,
            capabilities=tuple(self._capabilities), healthy=self._healthy)
    def execute_preview(self, request: ProviderRequest) -> ProviderResponse:
        actions = []
        if request.envelope:
            for item in request.envelope.items:
                actions.append(f"[{self._provider_type}] {item.action} -> {item.target}")
        return ProviderResponse(success=True, preview="; ".join(actions),
            estimated_duration=len(request.envelope.items) if request.envelope else 0,
            affected_resources=tuple(i.target for i in request.envelope.items) if request.envelope else (),
            rollback_available=True, provider_type=self._provider_type)
    def supported_actions(self) -> Tuple[str, ...]:
        acts: List[str] = []
        for c in self._capabilities: acts.extend(c.actions)
        return tuple(dict.fromkeys(acts))
    def health(self) -> ProviderMetadata: return self.metadata
    def add_capability(self, cap: ProviderCapability) -> None: self._capabilities.append(cap)
    def set_health(self, healthy: bool) -> None: self._healthy = healthy
