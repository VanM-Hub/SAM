# OP-422 — Plugin SDK
# Python 3.8, frozen DTO, synchronous

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime


@dataclass(frozen=True)
class PluginManifestS:
    name: str = ""; version: str = ""
    description: str = ""; author: str = ""
    capabilities: Tuple[Dict[str, Any], ...] = field(default_factory=tuple)
    dependencies: Tuple[str, ...] = field(default_factory=tuple)
    read_only: bool = True; requires_approval: bool = True


@dataclass(frozen=True)
class PluginValidationS:
    valid: bool = True
    errors: Tuple[str, ...] = field(default_factory=tuple)
    warnings: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class PluginTemplate:
    name: str = ""; description: str = ""
    template_type: str = "plugin"
    required_fields: Tuple[str, ...] = field(default_factory=tuple)
    template: str = ""


class PluginSDK:
    """SDK for developing plugins. No plugin execution."""

    def __init__(self):
        self._templates: Dict[str, PluginTemplate] = {}
        self._init_templates()

    def _init_templates(self):
        self._templates["minimal"] = PluginTemplate("Minimal Plugin","Basic plugin template","plugin",
            ("name","version","capabilities"),'{\n  "name": "my-plugin",\n  "version": "1.0.0",\n  "capabilities": []\n}')
        self._templates["analytics"] = PluginTemplate("Analytics Plugin","Plugin with read capabilities","plugin",
            ("name","version","capabilities"),'{\n  "name": "analytics",\n  "version": "1.0.0",\n  "read_only": true,\n  "capabilities": []\n}')

    def get_templates(self) -> Tuple[PluginTemplate, ...]: return tuple(self._templates.values())
    def get_template(self, name: str) -> Optional[PluginTemplate]: return self._templates.get(name)

    def build_manifest(self, name: str, version: str, description: str = "",
                       author: str = "", capabilities: Optional[Tuple[Dict, ...]] = None,
                       dependencies: Optional[Tuple[str, ...]] = None,
                       read_only: bool = True) -> PluginManifestS:
        return PluginManifestS(name=name, version=version, description=description,
            author=author, capabilities=capabilities or (), dependencies=dependencies or (),
            read_only=read_only)

    def validate_manifest(self, manifest: PluginManifestS) -> PluginValidationS:
        errors: List[str]=[]; warnings: List[str]=[]
        if not manifest.name: errors.append("Plugin name required")
        if not manifest.version: errors.append("Plugin version required")
        if not manifest.capabilities: warnings.append("Plugin has no capabilities")
        for cap in manifest.capabilities:
            if not cap.get("name"): errors.append("Capability name required")
            if not cap.get("actions"): warnings.append(f"Capability '{cap.get('name','?')}' has no actions")
        if not manifest.read_only and not manifest.requires_approval:
            errors.append("Non-readonly plugin must require approval")
        return PluginValidationS(valid=len(errors)==0, errors=tuple(errors), warnings=tuple(warnings))

    def create_plugin(self, manifest: PluginManifestS) -> Tuple[str, ...]:
        errors = self.validate_manifest(manifest)
        return errors.errors
