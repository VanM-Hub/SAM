# OP-392 — Connector Protocol
# Python 3.8 compatible, frozen dataclass, synchronous only
# Abstract protocol for execution connectors
# No network calls, no execution, no side effects

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple, Protocol
import uuid

from .execution_request import (
    ExecutionRequest,
    ExecutionTarget,
    ExecutionParameter,
    ExecutionPlan,
    ExecutionResult,
    ExecutionStatus,
    ExecutionRisk,
)


# ---------------------------------------------------------------------------
# Connector Metadata
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ConnectorCapability:
    """Describes a capability of a connector."""
    action: str = ""
    description: str = ""
    requires_approval: bool = True
    risk_level: str = "low"  # low, medium, high, critical
    estimated_duration_seconds: int = 0
    parameters: Tuple[ExecutionParameter, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ConnectorInfo:
    """Metadata about a connector implementation."""
    connector_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    connector_type: str = ""
    version: str = "1.0.0"
    description: str = ""
    capabilities: Tuple[ConnectorCapability, ...] = field(default_factory=tuple)
    healthy: bool = True
    health_message: str = ""


# ---------------------------------------------------------------------------
# Connector Protocol
# ---------------------------------------------------------------------------

class ConnectorProtocol(Protocol):
    """Protocol for execution connectors.

    All methods are read-only/validation/preview — NO network calls,
    NO execution, NO side effects.

    Implementations must be stateless (pure validation + DTO building).
    """

    @property
    def info(self) -> ConnectorInfo:
        """Return connector metadata."""
        ...

    def validate(self, request: ExecutionRequest) -> Tuple[str, ...]:
        """Validate an execution request. Returns list of validation errors.
        Empty tuple means valid.
        """
        ...

    def build_request(
        self,
        action: str,
        target: ExecutionTarget,
        parameters: Optional[Tuple[ExecutionParameter, ...]] = None,
    ) -> ExecutionRequest:
        """Build an ExecutionRequest for the given action and target.

        Must NOT execute anything — only creates an immutable DTO.
        """
        ...

    def preview(self, request: ExecutionRequest) -> str:
        """Generate a human-readable preview of what the execution would do.

        Must NOT execute anything — only returns a description.
        """
        ...

    def supported_actions(self) -> Tuple[str, ...]:
        """Return list of actions this connector supports."""
        ...

    def health(self) -> ConnectorInfo:
        """Return current health status of this connector.

        Must NOT make network calls — use cached/static info.
        """
        ...

    def version(self) -> str:
        """Return connector version string."""
        ...


# ---------------------------------------------------------------------------
# Base Connector (for convenience — not required, but useful)
# ---------------------------------------------------------------------------

class BaseConnector:
    """Base class for connectors that need minimal boilerplate.

    This is a CONVENIENCE base — not required.
    Connectors only need to implement ConnectorProtocol.
    """

    def __init__(
        self,
        name: str,
        connector_type: str,
        version: str = "1.0.0",
        description: str = "",
    ) -> None:
        self._connector_id = str(uuid.uuid4())
        self._name = name
        self._connector_type = connector_type
        self._version = version
        self._description = description
        self._capabilities: List[ConnectorCapability] = []
        self._healthy = True
        self._health_message = ""

    @property
    def info(self) -> ConnectorInfo:
        return ConnectorInfo(
            connector_id=self._connector_id,
            name=self._name,
            connector_type=self._connector_type,
            version=self._version,
            description=self._description,
            capabilities=tuple(self._capabilities),
            healthy=self._healthy,
            health_message=self._health_message,
        )

    def validate(self, request: ExecutionRequest) -> Tuple[str, ...]:
        """Validate an execution request. Override in subclass."""
        errors: List[str] = []
        if not request.action:
            errors.append("Action is required")
        if request.connector_type != self._connector_type:
            errors.append(f"Connector type mismatch: expected {self._connector_type}, got {request.connector_type}")
        if request.target is None:
            errors.append("Target is required")
        return tuple(errors)

    def build_request(
        self,
        action: str,
        target: ExecutionTarget,
        parameters: Optional[Tuple[ExecutionParameter, ...]] = None,
    ) -> ExecutionRequest:
        """Build an ExecutionRequest."""
        return ExecutionRequest(
            connector_type=self._connector_type,
            action=action,
            target=target,
            parameters=parameters or (),
        )

    def preview(self, request: ExecutionRequest) -> str:
        """Generate a preview string."""
        return request.as_preview()

    def supported_actions(self) -> Tuple[str, ...]:
        return tuple(c.action for c in self._capabilities)

    def health(self) -> ConnectorInfo:
        return self.info

    def version(self) -> str:
        return self._version

    def add_capability(self, capability: ConnectorCapability) -> None:
        """Add a capability (mutable during initialization only)."""
        self._capabilities.append(capability)

    def set_health(self, healthy: bool, message: str = "") -> None:
        """Set health status (for runtime health updates)."""
        self._healthy = healthy
        self._health_message = message
