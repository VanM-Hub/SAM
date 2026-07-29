# OP-411 — Plugin Protocol
# Python 3.8, frozen DTO, synchronous

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple, Protocol
import uuid


@dataclass(frozen=True)
class PluginCapability:
    name: str = ""; description: str = ""
    actions: Tuple[str, ...] = field(default_factory=tuple)
    requires_approval: bool = True
    risk_level: str = "low"
    read_only: bool = True


@dataclass(frozen=True)
class PluginDescriptor:
    plugin_id: str = ""
    name: str = ""; version: str = ""
    description: str = ""
    author: str = ""
    capabilities: Tuple[PluginCapability, ...] = field(default_factory=tuple)
    dependencies: Tuple[str, ...] = field(default_factory=tuple)
    healthy: bool = True
    enabled: bool = True


@dataclass(frozen=True)
class PluginMetadata:
    plugin_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""; version: str = ""
    description: str = ""
    capability_names: Tuple[str, ...] = field(default_factory=tuple)
    healthy: bool = True


@dataclass(frozen=True)
class PluginContext:
    context_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    plugin_id: str = ""
    session_id: str = ""
    status: str = "active"


@dataclass(frozen=True)
class PluginHealth:
    healthy: bool = True; plugin_id: str = ""
    name: str = ""; version: str = ""
    message: str = ""
    last_check: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class PluginLifecycle:
    plugin_id: str = ""
    enabled: bool = True
    healthy: bool = True
    loaded_count: int = 0
    last_loaded: Optional[datetime] = None
    status: str = "active"


@dataclass(frozen=True)
class PluginResult:
    result_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    success: bool = False
    preview: str = ""
    plugin_id: str = ""
    action: str = ""
    read_only: bool = True
    requires_approval: bool = True


class PluginProtocol(Protocol):
    @property
    def descriptor(self) -> PluginDescriptor: ...
    def execute_preview(self, action: str, params: Dict[str, Any]) -> PluginResult: ...
    def supported_actions(self) -> Tuple[str, ...]: ...
    def health(self) -> PluginHealth: ...
