# OP-424 — Provider SDK
# Python 3.8, frozen DTO, synchronous

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple


@dataclass(frozen=True)
class ProviderManifest:
    name: str = ""; version: str = ""
    provider_type: str = ""
    description: str = ""
    capabilities: Tuple[Dict[str, Any], ...] = field(default_factory=tuple)
    preview_only: bool = True


@dataclass(frozen=True)
class ProviderValidationS:
    valid: bool = True; errors: Tuple[str, ...] = field(default_factory=tuple)
    warnings: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ProviderTemplate:
    name: str = ""; description: str = ""
    provider_type: str = ""
    required_fields: Tuple[str, ...] = field(default_factory=tuple)
    template: str = ""


class ProviderSDK:
    def __init__(self):
        self._templates: Dict[str, ProviderTemplate] = {
            "filesystem": ProviderTemplate("Filesystem Provider","File operations","filesystem",
                ("name","actions"), '{"name":"fs-provider","provider_type":"filesystem"}'),
            "http": ProviderTemplate("HTTP Provider","REST API calls","http",
                ("name","endpoints"), '{"name":"http-provider","provider_type":"http"}'),
        }

    def get_templates(self): return tuple(self._templates.values())
    def get_template(self, name): return self._templates.get(name)

    def build_manifest(self, name, provider_type, version="1.0.0", description="", capabilities=None):
        return ProviderManifest(name=name, version=version, provider_type=provider_type,
            description=description, capabilities=capabilities or ())

    def validate_manifest(self, manifest: ProviderManifest) -> ProviderValidationS:
        errors = []; warnings = []
        if not manifest.name: errors.append("Provider name required")
        if not manifest.provider_type: errors.append("Provider type required")
        for cap in manifest.capabilities:
            if not cap.get("name"): errors.append("Capability name required")
        return ProviderValidationS(valid=len(errors)==0, errors=tuple(errors), warnings=tuple(warnings))
