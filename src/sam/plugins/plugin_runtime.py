# OP-415 — Plugin Runtime
# Python 3.8, frozen DTO, synchronous, preview only

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
import uuid

from .plugin_protocol import PluginProtocol, PluginDescriptor, PluginResult
from .plugin_registry import PluginRegistry, PluginEntry
from .plugin_loader import PluginLoader, PluginManifest, PluginPackage
from .plugin_policy import PluginPolicyEngine, PluginPolicyResult

from .conversation_plugin import ConversationPluginBridge, PluginQueryResult
from .dashboard_plugin import PluginDashboardBuilder, PluginDashboard


@dataclass(frozen=True)
class PluginRuntimeResult:
    pipeline_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    plugin_result: Optional[PluginResult] = None
    policy_result: Optional[PluginPolicyResult] = None
    conversation_result: Optional[PluginQueryResult] = None
    dashboard: Optional[PluginDashboard] = None
    pipeline_complete: bool = False; error: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)


class PluginRuntime:
    """Pipeline: Registry → Loader → Policy → Runtime → Conversation → Dashboard."""

    def __init__(self, registry: Optional[PluginRegistry] = None,
                 loader: Optional[PluginLoader] = None,
                 policy: Optional[PluginPolicyEngine] = None,
                 conversation: Optional[ConversationPluginBridge] = None,
                 dashboard: Optional[PluginDashboardBuilder] = None):
        self._registry = registry or PluginRegistry()
        self._loader = loader or PluginLoader()
        self._policy = policy or PluginPolicyEngine()
        self._conversation = conversation or ConversationPluginBridge(
            self._registry, self._policy)
        self._dashboard = dashboard or PluginDashboardBuilder()

    def register_plugin(self, plugin: PluginProtocol) -> PluginEntry:
        return self._registry.register(plugin)

    def execute_preview(self, plugin_id: str, action: str,
                        params: Optional[Dict[str, Any]] = None) -> PluginRuntimeResult:
        try:
            plugin = self._registry.find(plugin_id)
            if not plugin:
                return PluginRuntimeResult(pipeline_complete=False, error=f"Plugin '{plugin_id}' not found")

            d = plugin.descriptor
            result = plugin.execute_preview(action, params or {})
            policy = self._policy.evaluate(plugin_name=d.name, action=action,
                read_only=result.read_only, healthy=d.healthy, enabled=d.enabled)

            conv = self._conversation.query("plugin diagnostics")
            dash = self._dashboard.build(self._registry, self._policy)

            return PluginRuntimeResult(plugin_result=result, policy_result=policy,
                conversation_result=conv, dashboard=dash, pipeline_complete=True)

        except Exception as e:
            return PluginRuntimeResult(pipeline_complete=False, error=str(e))
