# OP-423 — Connector SDK
# Python 3.8, frozen DTO, synchronous

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple


@dataclass(frozen=True)
class ConnectorManifest:
    name: str = ""; version: str = ""
    connector_type: str = ""
    description: str = ""
    capabilities: Tuple[Dict[str, Any], ...] = field(default_factory=tuple)
    requires_approval: bool = True
    supports_preview: bool = True


@dataclass(frozen=True)
class ConnectorValidationS:
    valid: bool = True; errors: Tuple[str, ...] = field(default_factory=tuple)
    warnings: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ConnectorTemplate:
    name: str = ""; description: str = ""
    connector_type: str = ""
    required_fields: Tuple[str, ...] = field(default_factory=tuple)
    template: str = ""


class ConnectorSDK:
    def __init__(self):
        self._templates: Dict[str, ConnectorTemplate] = {
            "filesystem": ConnectorTemplate("Filesystem Connector","Read/write files","filesystem",
                ("name","actions"), '{"name":"fs-connector","connector_type":"filesystem","capabilities":[]}'),
            "rest_api": ConnectorTemplate("REST API Connector","HTTP API calls","rest_api",
                ("name","endpoints"), '{"name":"rest-connector","connector_type":"rest_api","capabilities":[]}'),
        }

    def get_templates(self) -> Tuple[ConnectorTemplate, ...]: return tuple(self._templates.values())
    def get_template(self, name: str) -> Optional[ConnectorTemplate]: return self._templates.get(name)

    def build_manifest(self, name: str, connector_type: str, version: str = "1.0.0",
                       description: str = "", capabilities=None) -> ConnectorManifest:
        return ConnectorManifest(name=name, version=version, connector_type=connector_type,
            description=description, capabilities=capabilities or ())

    def validate_manifest(self, manifest: ConnectorManifest) -> ConnectorValidationS:
        errors: List[str]=[]; warnings: List[str]=[]
        if not manifest.name: errors.append("Connector name required")
        if not manifest.connector_type: errors.append("Connector type required")
        if not manifest.capabilities: warnings.append("No capabilities defined")
        for cap in manifest.capabilities:
            if not cap.get("name"): errors.append("Capability name required")
        return ConnectorValidationS(valid=len(errors)==0, errors=tuple(errors), warnings=tuple(warnings))
