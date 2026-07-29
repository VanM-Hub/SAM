# OP-418 — Integration Plugin Pipeline
# Python 3.8, frozen DTO, synchronous, preview only

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
import uuid

from .plugin_protocol import PluginProtocol, PluginDescriptor, PluginResult, PluginCapability
from .plugin_registry import PluginRegistry, PluginEntry
from .plugin_loader import PluginLoader, PluginManifest
from .plugin_policy import PluginPolicyEngine, PluginPolicyResult
from .plugin_runtime import PluginRuntime, PluginRuntimeResult
from .conversation_plugin import ConversationPluginBridge, PluginQueryResult
from .dashboard_plugin import PluginDashboardBuilder, PluginDashboard


@dataclass(frozen=True)
class PluginPipelineResult:
    pipeline_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    runtime: Optional[PluginRuntimeResult] = None
    dashboard: Optional[PluginDashboard] = None
    pipeline_complete: bool = False; error: str = ""


class BasePlugin:
    """Base plugin for mock/testing — preview only."""

    def __init__(self, name: str, version: str = "1.0.0",
                 description: str = "", author: str = "system"):
        self._id = name.lower().replace(" ","_")
        self._name = name; self._version = version
        self._description = description; self._author = author
        self._capabilities: list = []
        self._healthy = True; self._enabled = True

    @property
    def descriptor(self) -> PluginDescriptor:
        return PluginDescriptor(plugin_id=self._id, name=self._name,
            version=self._version, description=self._description,
            author=self._author, capabilities=tuple(self._capabilities),
            healthy=self._healthy, enabled=self._enabled)

    def execute_preview(self, action: str, params: Dict[str, Any]) -> PluginResult:
        cap = None
        for c in self._capabilities:
            if action in c.actions: cap = c; break
        read_only = cap.read_only if cap else True
        req_appr = cap.requires_approval if cap else True
        return PluginResult(success=True, preview=f"[{self._name}] {action} -> {params.get('target','unknown')}",
            plugin_id=self._id, action=action, read_only=read_only, requires_approval=req_appr)

    def supported_actions(self) -> Tuple[str, ...]:
        acts = []; [acts.extend(c.actions) for c in self._capabilities]
        return tuple(dict.fromkeys(acts))

    def health(self): from .plugin_protocol import PluginHealth; return PluginHealth(
        healthy=self._healthy, plugin_id=self._id, name=self._name, version=self._version)

    def add_capability(self, cap): self._capabilities.append(cap)
    def set_healthy(self, h): self._healthy = h
    def set_enabled(self, e): self._enabled = e


class MockAnalyticsPlugin(BasePlugin):
    def __init__(self):
        super().__init__("Analytics Plugin", "1.0.0", "Data analytics", "SAM")
        self.add_capability(PluginCapability("analyze","Analyze data",("read","search"),False,"low",True))
        self.add_capability(PluginCapability("report","Generate report",("read",),False,"low",True))


class MockExportPlugin(BasePlugin):
    def __init__(self):
        super().__init__("Export Plugin", "1.0.0", "Data export", "SAM")
        self.add_capability(PluginCapability("export","Export data",("read","write"),True,"medium",True))
        self.add_capability(PluginCapability("format","Format data",("write",),True,"medium",True))


class MockMonitorPlugin(BasePlugin):
    def __init__(self):
        super().__init__("Monitor Plugin", "1.0.0", "System monitoring", "SAM")
        self.add_capability(PluginCapability("monitor","Monitor resources",("read","monitor"),False,"low",True))
        self.add_capability(PluginCapability("alert","Send alerts",("notify",),True,"low",False))
