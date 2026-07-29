# OP-401 — Integration Contracts
# Python 3.8, frozen DTO, synchronous, preview only

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple, Protocol
import uuid


@dataclass(frozen=True)
class IntegrationCapability:
    name: str = ""; description: str = ""
    actions: Tuple[str, ...] = field(default_factory=tuple)
    integration_type: str = ""
    requires_approval: bool = True
    risk_level: str = "low"


@dataclass(frozen=True)
class IntegrationDescriptor:
    integration_id: str = ""
    integration_type: str = ""
    name: str = ""; version: str = ""
    healthy: bool = True
    capability_names: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class IntegrationRequest:
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    integration_type: str = ""
    action: str = ""
    target: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class IntegrationPreview:
    preview_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    success: bool = False
    summary: str = ""
    estimated_duration: int = 0
    affected_resources: Tuple[str, ...] = field(default_factory=tuple)
    can_rollback: bool = True
    integration_type: str = ""


@dataclass(frozen=True)
class IntegrationResponse:
    response_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    success: bool = False
    preview: Optional[IntegrationPreview] = None
    error: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class IntegrationHealth:
    healthy: bool = True
    integration_type: str = ""
    name: str = ""; version: str = ""
    message: str = ""
    last_check: datetime = field(default_factory=datetime.utcnow)


class IntegrationProtocol(Protocol):
    @property
    def descriptor(self) -> IntegrationDescriptor: ...
    def preview(self, request: IntegrationRequest) -> IntegrationResponse: ...
    def supported_actions(self) -> Tuple[str, ...]: ...
    def health(self) -> IntegrationHealth: ...
