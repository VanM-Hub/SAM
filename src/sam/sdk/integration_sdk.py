# OP-428 — Integration SDK Pipeline
# Python 3.8, frozen DTO, synchronous, preview only

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
import uuid

from .sdk_protocol import SDKVersion, SDKMetadata, SDKResult
from .plugin_sdk import PluginSDK, PluginManifestS
from .connector_sdk import ConnectorSDK, ConnectorManifest
from .provider_sdk import ProviderSDK, ProviderManifest
from .extension_validator import ExtensionValidator, CompatibilityReport
from .conversation_sdk import ConversationSDKBridge, SDKQueryResult
from .dashboard_sdk import SDKDashboardBuilder, SDKDashboard


@dataclass(frozen=True)
class SDKPipelineResult:
    pipeline_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    compatibility: Optional[CompatibilityReport] = None
    conversation: Optional[SDKQueryResult] = None
    dashboard: Optional[SDKDashboard] = None
    pipeline_complete: bool = False; error: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)


class SDKPipeline:
    """Pipeline: SDK → Extension Validator → Compatibility → Conversation → Dashboard."""

    def __init__(self, psdk: Optional[PluginSDK] = None, csdk: Optional[ConnectorSDK] = None,
                 prsdk: Optional[ProviderSDK] = None,
                 validator: Optional[ExtensionValidator] = None,
                 conversation: Optional[ConversationSDKBridge] = None,
                 dashboard: Optional[SDKDashboardBuilder] = None):
        self._psdk = psdk or PluginSDK(); self._csdk = csdk or ConnectorSDK()
        self._prsdk = prsdk or ProviderSDK()
        self._v = validator or ExtensionValidator()
        self._conversation = conversation or ConversationSDKBridge(self._psdk,self._csdk,self._prsdk,self._v)
        self._dashboard = dashboard or SDKDashboardBuilder()

    def validate_plugin(self, name: str, version: str, capabilities=None,
                        read_only: bool = True) -> SDKPipelineResult:
        try:
            manifest = self._psdk.build_manifest(name, version, capabilities=capabilities, read_only=read_only)
            report = self._v.validate_plugin_manifest(manifest)
            conv = self._conversation.query("SDK version")
            dash = self._dashboard.build(self._psdk, self._csdk, self._prsdk, self._v)
            return SDKPipelineResult(compatibility=report, conversation=conv, dashboard=dash, pipeline_complete=True)
        except Exception as e:
            return SDKPipelineResult(pipeline_complete=False, error=str(e))
