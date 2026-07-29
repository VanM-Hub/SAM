# OP-432 — Adapter Protocol
# Python 3.8, frozen DTO, synchronous, preview only

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple, Protocol
import uuid

from .execution_envelope import ExecutionEnvelope, ExecutionEnvelopeItem


@dataclass(frozen=True)
class AdapterCapability:
    name: str = ""
    description: str = ""
    actions: Tuple[str, ...] = field(default_factory=tuple)
    adapter_type: str = ""
    requires_approval: bool = True
    supports_preview: bool = True
    risk_level: str = "low"


@dataclass(frozen=True)
class AdapterContext:
    context_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    adapter_type: str = ""
    envelope_id: str = ""
    started_at: datetime = field(default_factory=datetime.utcnow)
    status: str = "active"


@dataclass(frozen=True)
class AdapterResult:
    result_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    success: bool = False
    preview: str = ""
    estimated_resources: Dict[str, Any] = field(default_factory=dict)
    rollback_steps: Tuple[str, ...] = field(default_factory=tuple)
    error: str = ""


@dataclass(frozen=True)
class AdapterHealth:
    healthy: bool = True
    adapter_type: str = ""
    adapter_name: str = ""
    version: str = "1.0.0"
    message: str = ""
    last_check: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class AdapterMetadata:
    adapter_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    adapter_type: str = ""
    name: str = ""
    version: str = "1.0.0"
    description: str = ""
    capabilities: Tuple[AdapterCapability, ...] = field(default_factory=tuple)
    healthy: bool = True


class ExecutionAdapterProtocol(Protocol):
    """Protocol for execution adapters.

    All methods are read-only/preview — NO network calls, NO execution.
    """

    @property
    def metadata(self) -> AdapterMetadata:
        ...

    def validate(self, envelope: ExecutionEnvelope) -> Tuple[str, ...]:
        """Validate envelope compatibility. Returns errors."""
        ...

    def preview(self, envelope: ExecutionEnvelope) -> AdapterResult:
        """Generate a preview of what execution would do. No side effects."""
        ...

    def supported_actions(self) -> Tuple[str, ...]:
        ...

    def health(self) -> AdapterHealth:
        ...


class BaseAdapter:
    """Base class for adapters — convenience, not required."""

    def __init__(self, adapter_type: str, name: str, version: str = "1.0.0",
                 description: str = ""):
        self._adapter_id = str(uuid.uuid4())
        self._adapter_type = adapter_type
        self._name = name
        self._version = version
        self._description = description
        self._capabilities: List[AdapterCapability] = []
        self._healthy = True

    @property
    def metadata(self) -> AdapterMetadata:
        return AdapterMetadata(
            adapter_id=self._adapter_id, adapter_type=self._adapter_type,
            name=self._name, version=self._version,
            description=self._description,
            capabilities=tuple(self._capabilities),
            healthy=self._healthy,
        )

    def validate(self, envelope: ExecutionEnvelope) -> Tuple[str, ...]:
        errors: List[str] = []
        if not envelope.items:
            errors.append("Envelope has no items")
        for item in envelope.items:
            if item.adapter_type and item.adapter_type != self._adapter_type:
                errors.append(f"Item adapter type mismatch: {item.adapter_type} != {self._adapter_type}")
        return tuple(errors)

    def preview(self, envelope: ExecutionEnvelope) -> AdapterResult:
        previews: List[str] = []
        for item in envelope.items:
            previews.append(f"[{self._adapter_type}] {item.action} -> {item.target}")
        return AdapterResult(
            success=True,
            preview="; ".join(previews),
            estimated_resources={"cpu": "low", "memory": "low"},
            rollback_steps=tuple(f"rollback {item.action}" for item in envelope.items),
        )

    def supported_actions(self) -> Tuple[str, ...]:
        actions: List[str] = []
        for cap in self._capabilities:
            actions.extend(cap.actions)
        return tuple(dict.fromkeys(actions))

    def health(self) -> AdapterHealth:
        return AdapterHealth(
            healthy=self._healthy, adapter_type=self._adapter_type,
            adapter_name=self._name, version=self._version,
        )

    def add_capability(self, capability: AdapterCapability) -> None:
        self._capabilities.append(capability)

    def set_health(self, healthy: bool, message: str = "") -> None:
        self._healthy = healthy


class MockAdapter(BaseAdapter):
    """Mock adapter for testing — preview only."""

    def __init__(self):
        super().__init__("mock", "Mock Adapter", "1.0.0", "Mock adapter for testing")
        self.add_capability(AdapterCapability(
            name="filesystem", description="File operations",
            actions=("read","write","create","delete","search"),
            adapter_type="mock", supports_preview=True,
        ))
        self.add_capability(AdapterCapability(
            name="rest_api", description="REST API operations",
            actions=("read","write","create","delete","monitor","notify"),
            adapter_type="mock", supports_preview=True,
        ))
        self.add_capability(AdapterCapability(
            name="shell", description="Shell operations",
            actions=("read","monitor","execute","search"),
            adapter_type="mock", requires_approval=True, risk_level="high",
            supports_preview=True,
        ))
