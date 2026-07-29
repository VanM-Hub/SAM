# OP-426 — Conversation SDK Bridge
# Python 3.8, frozen DTO, synchronous

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, Tuple

from .sdk_protocol import SDKVersion, SDKMetadata, SDKCompatibility
from .plugin_sdk import PluginSDK, PluginTemplate
from .connector_sdk import ConnectorSDK, ConnectorTemplate
from .provider_sdk import ProviderSDK, ProviderTemplate
from .extension_validator import ExtensionValidator, CompatibilityReport


@dataclass(frozen=True)
class SDKQueryResult:
    query_type: str = ""; data: Any = None; count: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ConversationSDKBridge:
    """10 query types: SDK version, installed extensions, compatibility,
    validation, templates, plugin SDK, connector SDK, provider SDK,
    extension diagnostics, migration guide."""

    def __init__(self, plugin_sdk: PluginSDK, connector_sdk: ConnectorSDK,
                 provider_sdk: ProviderSDK, validator: ExtensionValidator):
        self._psdk = plugin_sdk; self._csdk = connector_sdk
        self._prsdk = provider_sdk; self._v = validator

    def query(self, qt: str, params: Optional[Dict]=None) -> SDKQueryResult:
        params = params or {}
        handlers = {
            "sdk version": self._q_version, "installed extensions": self._q_extensions,
            "compatibility": self._q_compat, "validation": self._q_validation,
            "templates": self._q_templates, "plugin sdk": self._q_plugin,
            "connector sdk": self._q_connector, "provider sdk": self._q_provider,
            "extension diagnostics": self._q_diag, "migration guide": self._q_migrate,
        }
        handler = handlers.get(qt.lower())
        if not handler: return SDKQueryResult(qt,{"error":f"Unknown: {qt}"},0)
        return handler(params)

    def _q_version(self, p): v=SDKVersion.current(); return SDKQueryResult("SDK version",{"version":str(v)},1)
    def _q_extensions(self, p): return SDKQueryResult("installed extensions",{"types":["plugin","connector","provider","adapter","integration"]},5)
    def _q_compat(self, p):
        r=self._v.check_sdk_compatibility(p.get("sdk_version"),p.get("python_version","3.8"),p.get("sam_version","4.45.0"))
        return SDKQueryResult("compatibility",{"compatible":r.compatible,"issues":list(r.issues)},1)
    def _q_validation(self, p): return SDKQueryResult("validation",{"note":"Use ExtensionValidator"},0)
    def _q_templates(self, p):
        all_templates=[]
        for t in self._psdk.get_templates(): all_templates.append({"type":"plugin","name":t.name})
        for t in self._csdk.get_templates(): all_templates.append({"type":"connector","name":t.name})
        for t in self._prsdk.get_templates(): all_templates.append({"type":"provider","name":t.name})
        return SDKQueryResult("templates",{"templates":all_templates},len(all_templates))
    def _q_plugin(self, p):
        caps=len(self._psdk.get_templates()); return SDKQueryResult("plugin SDK",{"templates":caps},1)
    def _q_connector(self, p):
        caps=len(self._csdk.get_templates()); return SDKQueryResult("connector SDK",{"templates":caps},1)
    def _q_provider(self, p):
        caps=len(self._prsdk.get_templates()); return SDKQueryResult("provider SDK",{"templates":caps},1)
    def _q_diag(self, p): return SDKQueryResult("extension diagnostics",
        {"plugin_templates":len(self._psdk.get_templates()),
         "connector_templates":len(self._csdk.get_templates()),
         "provider_templates":len(self._prsdk.get_templates())},1)
    def _q_migrate(self, p): return SDKQueryResult("migration guide",
        {"note":"Use SDKProtocol to build extensions","version":"1.0.0"},1)
